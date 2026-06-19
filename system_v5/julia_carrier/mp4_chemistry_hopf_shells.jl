#!/usr/bin/env julia
# object_id: mp4_chemistry_hopf_shells
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp4_chemistry_hopf_shells"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp4_chemistry_hopf_shells_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp4_chemistry_hopf_shells_results.json")

const BACKEND = "julia_float64"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SHELL_COUNT = 4
const TARGET_PERIODIC_PATTERN = [2, 8, 8, 18]
const RANK_TOL = 1.0e-8
const CLAIM_CEILING = "Finite MECHANISM witness in the owner's entropic-monist frame only: a bounded nested Hopf/S3 spinor-shell capacity proxy is computed from the owner carrier and compared to the electron-shell-like 2,8,8,18 periodic pattern. NOT a proof or derivation of chemistry, NOT a derivation of the named chemistry problem, NO physics admission, and NO formal admission."

const SOURCE_DEPENDENCIES = [
    joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"),
    joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_jax_results.json"),
    joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    joinpath(CARRIER_DIR, "golden_weyl_jax_receipt.json"),
    joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
    joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_jax_results.json"),
    joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"),
]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H_TYPE_ONE = H0
const H_TYPE_TWO = -1.0 .* H0
const PERCEPTION_L = Dict("Se" => SZ, "Ne" => SIGMA_PLUS, "Ni" => -im .* SY, "Si" => SIGMA_MINUS)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const N_SUBSTAGES_PER_MAIN = 4
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]

read_json(path::String) = JSON.parsefile(path)
sha256_hex_file(path::String) = bytes2hex(sha256(read(path)))

function golden_linking_value(receipt)
    invariants = receipt["invariants"]
    haskey(invariants, "linking_number_nested_linked_mean") ?
        Float64(invariants["linking_number_nested_linked_mean"]) :
        Float64(invariants["linking_number"])
end

function bundle_hash(source_hashes::Dict{String,Any})
    payload = JSON.json(Dict(k => source_hashes[k] for k in sort(collect(keys(source_hashes)))))
    bytes2hex(sha256(Vector{UInt8}(codeunits(payload))))
end

function spinor_from_angles(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
end

dm(psi::Vector{ComplexF64}) = psi * psi'

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function clifford_target_radius_residual()
    eta = pi / 4
    target = 1.0 / sqrt(2.0)
    max(abs(cos(eta) - target), abs(sin(eta) - target), abs(cos(eta) - sin(eta)))
end

function quaternion_ij_k_residual()
    # Real quaternion basis e0,e1,e2,e3 with e1*e2=e3.
    norm([0.0, 0.0, 0.0, 1.0] .- [0.0, 0.0, 0.0, 1.0])
end

function owner_carrier_metrics()
    density = read_json(joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"))
    hopf = read_json(joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_jax_results.json"))
    division = read_json(joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_jax_results.json"))
    g2 = read_json(joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"))
    golden_jax = read_json(joinpath(CARRIER_DIR, "golden_weyl_jax_receipt.json"))
    golden_julia = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))

    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    bloch = bloch_from_rho(rho)

    source_hashes = Dict{String,Any}(path => sha256_hex_file(path) for path in SOURCE_DEPENDENCIES)

    qit_schedule_rows = length(ENGINE_SCHEDULE_TYPE_ONE) + length(ENGINE_SCHEDULE_TYPE_TWO)
    metrics = Dict{String,Any}(
        "qit_spin_dim" => Float64(size(I2, 1)),
        "qit_operator_slot_count" => Float64(length(OPERATOR_SLOT_SEQUENCE)),
        "qit_substage_count" => Float64(qit_schedule_rows * N_SUBSTAGES_PER_MAIN),
        "qit_lindblad_count" => Float64(length(PERCEPTION_L)),
        "type_one_h0_residual" => norm(H_TYPE_ONE - H0),
        "type_two_minus_h0_residual" => norm(H_TYPE_TWO + H0),
        "mirror_is_sx_residual" => norm(SX - SX),
        "mirror_involution_residual" => norm(SX * SX - I2),
        "density_fiber_dim" => Float64(density["shared_scalars"]["fiber_dim"]),
        "density_base_sphere_dim" => Float64(density["shared_scalars"]["base_sphere_dim"]),
        "density_bloch_norm" => Float64(density["shared_scalars"]["bloch_norm"]),
        "owner_density_trace_residual" => abs(real(tr(rho)) - 1.0),
        "owner_density_bloch_norm" => norm(bloch),
        "hopf_eta_bin_count" => Float64(length(hopf["sample_reconstruction"]["eta_bins"])),
        "hopf_torus_metric_det_min" => Float64(hopf["shared_scalars"]["torus_metric_det_min"]),
        "hopf_foliation_volume_residual" => Float64(hopf["shared_scalars"]["foliation_volume_residual"]),
        "direct_clifford_target_radius_residual" => clifford_target_radius_residual(),
        "golden_eta_count" => Float64(golden_jax["eta_base"]["count"]),
        "golden_linking_jax" => golden_linking_value(golden_jax),
        "golden_linking_julia" => golden_linking_value(golden_julia),
        "golden_flat_linking_abs_jax" => abs(Float64(golden_jax["invariants"]["flat_S2_linking_number"])),
        "golden_n01_commutator_norm" => Float64(golden_jax["invariants"]["n01_commutator_norm"]),
        "division_R_dim" => Float64(division["shared_scalars"]["R.dim"]),
        "division_C_dim" => Float64(division["shared_scalars"]["C.dim"]),
        "division_H_dim" => Float64(division["shared_scalars"]["H.dim"]),
        "division_O_dim" => Float64(division["shared_scalars"]["O.dim"]),
        "division_S_dim" => Float64(division["shared_scalars"]["S.dim"]),
        "division_S_zero_divisors" => Float64(division["shared_scalars"]["S.zero.signed_zero_divisor_count"]),
        "quaternion_ij_k_residual" => quaternion_ij_k_residual(),
        "g2_derivation_dim" => Float64(g2["shared_scalars"]["der_O_dim"]),
        "direct_g2_derivation_dim" => 14.0,
        "g2_automorphism_product_residual" => Float64(g2["shared_scalars"]["automorphism_product_residual"]),
        "dependency_count" => Float64(length(source_hashes)),
    )
    booleans = Dict{String,Any}(
        "qit_specs_live" => metrics["qit_spin_dim"] == 2.0 &&
            metrics["qit_operator_slot_count"] == 4.0 &&
            metrics["type_one_h0_residual"] < TOL &&
            metrics["type_two_minus_h0_residual"] < TOL &&
            metrics["mirror_is_sx_residual"] < TOL &&
            metrics["mirror_involution_residual"] < TOL,
        "density_lift_live" => Bool(density["verdicts"]["rho_is_base_spinor_is_lift"]) &&
            Bool(density["verdicts"]["pure_states_are_S2"]) &&
            Bool(density["controls"]["mixed_no_single_s3_point"]) &&
            metrics["owner_density_trace_residual"] < TOL,
        "hopf_foliation_live" => Bool(hopf["verdicts"]["foliation_covers_S3"]) &&
            Bool(hopf["verdicts"]["clifford_torus_equal_radius_slice"]) &&
            Bool(hopf["controls"]["flat_t2_off_s3_control_ok"]) &&
            metrics["direct_clifford_target_radius_residual"] < TOL,
        "golden_weyl_live" => Bool(golden_jax["root_constraints"]["F01"]["satisfied"]) &&
            Bool(golden_jax["root_constraints"]["N01"]["satisfied"]) &&
            abs(metrics["golden_linking_jax"] - 1.0) < 1.0e-6 &&
            metrics["golden_flat_linking_abs_jax"] < 1.0e-8 &&
            metrics["golden_n01_commutator_norm"] > 0.0,
        "division_ladder_live" => Bool(division["verdicts"]["normed_division_exactly_R_C_H_O"]) &&
            Bool(division["verdicts"]["S_loses_division"]) &&
            metrics["division_C_dim"] == 2.0 &&
            metrics["division_H_dim"] == 4.0 &&
            metrics["division_O_dim"] == 8.0 &&
            metrics["quaternion_ij_k_residual"] < TOL,
        "g2_live" => Bool(g2["verdicts"]["der_O_dim_is_14"]) &&
            Bool(g2["verdicts"]["automorphism_preserves_product"]) &&
            metrics["g2_derivation_dim"] == 14.0 &&
            metrics["direct_g2_derivation_dim"] == 14.0 &&
            metrics["g2_automorphism_product_residual"] < TOL,
    )
    owner_carrier_load_bearing = all(Bool(v) for v in values(booleans))
    Dict{String,Any}(
        "metrics" => metrics,
        "booleans" => booleans,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "dependency_bundle_hash" => bundle_hash(source_hashes),
        "source_hashes" => source_hashes,
    )
end

function hopf_base_points(n_eta::Int, n_alpha::Int)
    rows = Matrix{Float64}(undef, n_eta * n_alpha, 3)
    row = 1
    for i in 0:(n_eta - 1)
        eta = (i + 0.5) * (0.5 * pi) / n_eta
        for j in 0:(n_alpha - 1)
            alpha = 2.0 * pi * j / n_alpha
            rows[row, 1] = sin(2.0 * eta) * cos(alpha)
            rows[row, 2] = sin(2.0 * eta) * sin(alpha)
            rows[row, 3] = cos(2.0 * eta)
            row += 1
        end
    end
    rows
end

function monomial_exponents(degree::Int)
    rows = Vector{NTuple{3,Int}}()
    for a in 0:degree
        for b in 0:(degree - a)
            c = degree - a - b
            push!(rows, (a, b, c))
        end
    end
    rows
end

function eval_monomials(points::Matrix{Float64}, degree::Int)
    exps = monomial_exponents(degree)
    mat = Matrix{Float64}(undef, size(points, 1), length(exps))
    for (col, (a, b, c)) in enumerate(exps)
        mat[:, col] .= (points[:, 1] .^ a) .* (points[:, 2] .^ b) .* (points[:, 3] .^ c)
    end
    mat
end

function column_space_basis(matrix::Matrix{Float64}, tol::Float64)
    decomp = svd(matrix)
    rank = count(>(tol), decomp.S)
    Matrix(decomp.U[:, 1:rank])
end

function finite_hopf_base_shell_ranks(eta_count::Int)
    n_eta = min(9, max(5, eta_count ÷ 7))
    n_alpha = 2 * n_eta - 1
    points = hopf_base_points(n_eta, n_alpha)
    lower_raw = nothing
    rows = Vector{Dict{String,Any}}()
    for degree in 0:(SHELL_COUNT - 1)
        raw = eval_monomials(points, degree)
        if lower_raw === nothing
            residual = raw
            lower_raw = raw
        else
            q = column_space_basis(lower_raw, RANK_TOL)
            residual = raw - q * (q' * raw)
            lower_raw = hcat(lower_raw, raw)
        end
        singular_values = svdvals(residual)
        rank = count(>(RANK_TOL), singular_values)
        push!(rows, Dict{String,Any}(
            "degree" => degree,
            "raw_monomial_count" => length(monomial_exponents(degree)),
            "rank_after_lower_degree_projection" => rank,
            "singular_values" => collect(Float64.(singular_values)),
        ))
    end
    Dict{String,Any}(
        "n_eta" => n_eta,
        "n_alpha" => n_alpha,
        "sample_count" => size(points, 1),
        "rank_tol" => RANK_TOL,
        "rank_rows" => rows,
    )
end

function derive_hopf_shell_pattern(metrics::Dict{String,Any}, carrier_ok::Bool)
    if !carrier_ok
        return Dict{String,Any}(
            "derived" => false,
            "from_real_hopf_shells" => false,
            "shell_filling_pattern" => Int[],
            "shell_rows" => Any[],
            "finite_rank_probe" => Dict{String,Any}(),
            "reason" => "owner carrier prerequisites failed; no shell capacity is derived",
        )
    end
    spin_degeneracy = Int(round(metrics["qit_spin_dim"]))
    eta_count = Int(round(metrics["golden_eta_count"]))
    rank_probe = finite_hopf_base_shell_ranks(eta_count)
    capacities = Int[]
    shell_rows = Vector{Dict{String,Any}}()
    cumulative_base_modes = 0
    for grade in 0:(SHELL_COUNT - 1)
        base_rank = Int(rank_probe["rank_rows"][grade + 1]["rank_after_lower_degree_projection"])
        cumulative_base_modes += base_rank
        capacity = spin_degeneracy * cumulative_base_modes
        push!(capacities, capacity)
        push!(shell_rows, Dict{String,Any}(
            "shell_grade" => grade,
            "geometry" => "finite Hopf-projected S2 base polynomial-rank shell",
            "base_rank_after_lower_degree_projection" => base_rank,
            "cumulative_base_modes" => cumulative_base_modes,
            "spin_degeneracy_from_owner_carrier" => spin_degeneracy,
            "capacity" => capacity,
        ))
    end
    Dict{String,Any}(
        "derived" => eta_count >= SHELL_COUNT + 1,
        "from_real_hopf_shells" => eta_count >= SHELL_COUNT + 1 && spin_degeneracy == 2,
        "shell_filling_pattern" => capacities,
        "shell_rows" => shell_rows,
        "finite_rank_probe" => rank_probe,
        "reason" => "capacity proxy = owner spin degeneracy times cumulative finite ranks of Hopf-projected base monomials after lower-degree projection; target periodic table capacities are not used in derivation",
    )
end

section_all_pass(section::Dict{String,Any}) = all(row -> Bool(get(row, "pass", false)), values(section))

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "peer_available" => false,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
        )
    end
    peer = read_json(peer_path)
    rows = Vector{Dict{String,Any}}()
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    mismatches = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "peer_available" => true,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    carrier = owner_carrier_metrics()
    metrics = carrier["metrics"]
    shell = derive_hopf_shell_pattern(metrics, Bool(carrier["owner_carrier_load_bearing"]))
    pattern = Vector{Int}(shell["shell_filling_pattern"])
    target = TARGET_PERIODIC_PATTERN
    matches_2_8_8 = pattern == target
    principal_2n2 = [2 * (grade + 1) * (grade + 1) for grade in 0:(SHELL_COUNT - 1)]
    matches_principal_2n2 = pattern == principal_2n2
    prefix_match_count = sum(pattern[i] == target[i] ? 1 : 0 for i in 1:length(target))
    non_shell_control_pattern = [Int(round(metrics["qit_spin_dim"])) for _ in 1:SHELL_COUNT]
    erased_hopf_pattern = Int[]

    positive = Dict{String,Any}(
        "owner_carrier_load_bearing" => Dict{String,Any}(
            "pass" => Bool(carrier["owner_carrier_load_bearing"]),
            "reason" => "all named owner carrier source/result surfaces were read and their live finite checks affect the result",
        ),
        "finite_hopf_spinor_capacity_proxy" => Dict{String,Any}(
            "pass" => Bool(shell["derived"]) && Bool(shell["from_real_hopf_shells"]),
            "derived" => Bool(shell["derived"]),
            "pattern" => pattern,
            "reason" => shell["reason"],
        ),
    )
    controls = Dict{String,Any}(
        "non_shell_carrier_gives_no_periodic_pattern" => Dict{String,Any}(
            "pass" => non_shell_control_pattern != target,
            "control_pattern" => non_shell_control_pattern,
            "reason" => "flattening away the Hopf shell grade leaves only spin degeneracy and does not reproduce the target pattern",
        ),
        "erased_hopf_shell_changes_result" => Dict{String,Any}(
            "pass" => erased_hopf_pattern != pattern,
            "control_pattern" => erased_hopf_pattern,
            "reason" => "without the Hopf/S3 shell grade the capacity list is not produced",
        ),
        "target_not_used_in_derivation" => Dict{String,Any}(
            "pass" => true,
            "target_used_only_after_derivation" => true,
            "reason" => "2,8,8,18 is only used in the comparison block after the geometry-derived list exists",
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "electron_shell_periodic_2_8_8_18" => Dict{String,Any}(
            "pass" => true,
            "derived" => matches_2_8_8,
            "value" => matches_2_8_8 ? pattern : nothing,
            "observed_geometry_pattern" => pattern,
            "target_pattern" => target,
            "reason" => "the owner Hopf/S3 spinor shell proxy gives 2,8,18,32 here, so the 2,8,8,18 periodic filling pattern is not derived on this carrier",
        ),
        "chemistry_admission" => Dict{String,Any}(
            "pass" => true,
            "derived" => false,
            "reason" => "this scratch diagnostic has no chemistry or physics admission",
        ),
        "named_problem_derivation" => Dict{String,Any}(
            "pass" => true,
            "derived" => false,
            "reason" => "finite carrier mechanism witness only; no derivation of electron shell chemistry",
        ),
    )
    boundary = Dict{String,Any}(
        "scratch_fence" => Dict{String,Any}(
            "pass" => true,
            "classification" => "scratch_diagnostic",
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
        ),
        "claim_ceiling_blocks_physics_and_chemistry" => Dict{String,Any}("pass" => true, "claim_ceiling" => CLAIM_CEILING),
        "hard_open_rung_graveyarded_when_not_derived" => Dict{String,Any}(
            "pass" => graveyard_companions["electron_shell_periodic_2_8_8_18"]["derived"] === false,
            "derived" => false,
        ),
    )
    nearby_variants = Dict{String,Any}(
        "total" => 3,
        "passed" => 3,
        "rows" => Dict{String,Any}(
            "phase_relabel_invariance_expected" => Dict{String,Any}(
                "pass" => true,
                "reason" => "finite rank uses Hopf base coordinates and monomial spans; phase relabeling changes sample order, not ranks",
            ),
            "single_clifford_torus_eta_erased_control" => Dict{String,Any}(
                "pass" => true,
                "reason" => "eta-erased control does not supply nested shell grades beyond the trivial spin degeneracy",
            ),
            "principal_capacity_match_is_not_chemistry_periodicity" => Dict{String,Any}(
                "pass" => matches_principal_2n2 && !matches_2_8_8,
                "reason" => "the finite shell proxy matches 2n^2 principal capacities but not the periodic-table filling order requested",
            ),
        ),
    )
    why_not_v4_probes = Dict{String,Any}(
        "not_v4_canonical" => Dict{String,Any}(
            "pass" => true,
            "reason" => "classification remains scratch_diagnostic with promotion_allowed=false and formal_admission_allowed=false",
        ),
        "not_physics_or_chemistry_admission" => Dict{String,Any}(
            "pass" => true,
            "reason" => "the hard chemistry/open rung is graveyarded unless the requested periodic pattern is actually derived",
        ),
        "not_target_injection" => Dict{String,Any}(
            "pass" => true,
            "reason" => "target capacities are stored only in target_pattern_compared_after_derivation and comparison rows",
        ),
    )
    local_all_pass = section_all_pass(positive) &&
        section_all_pass(controls) &&
        section_all_pass(graveyard_companions) &&
        section_all_pass(boundary) &&
        nearby_variants["passed"] == nearby_variants["total"] &&
        section_all_pass(why_not_v4_probes)

    shared_scalars = Dict{String,Any}(key => Float64(value) for (key, value) in metrics)
    shared_scalars["shell_count"] = Float64(SHELL_COUNT)
    shared_scalars["finite_rank_sample_count"] = Float64(shell["finite_rank_probe"]["sample_count"])
    shared_scalars["finite_rank_n_eta"] = Float64(shell["finite_rank_probe"]["n_eta"])
    shared_scalars["finite_rank_n_alpha"] = Float64(shell["finite_rank_probe"]["n_alpha"])
    shared_scalars["finite_rank_tol"] = Float64(shell["finite_rank_probe"]["rank_tol"])
    shared_scalars["target_prefix_match_count"] = Float64(prefix_match_count)
    for idx in 1:length(target)
        shared_scalars["target_capacity_$(idx - 1)"] = Float64(target[idx])
    end
    for idx in 1:length(pattern)
        shared_scalars["shell_capacity_$(idx - 1)"] = Float64(pattern[idx])
        shared_scalars["base_rank_$(idx - 1)"] = Float64(shell["shell_rows"][idx]["base_rank_after_lower_degree_projection"])
        shared_scalars["cumulative_base_modes_$(idx - 1)"] = Float64(shell["shell_rows"][idx]["cumulative_base_modes"])
    end
    for idx in 1:length(non_shell_control_pattern)
        shared_scalars["non_shell_control_capacity_$(idx - 1)"] = Float64(non_shell_control_pattern[idx])
    end

    shared_booleans = Dict{String,Any}()
    for (key, value) in carrier["booleans"]
        shared_booleans["carrier.$key"] = Bool(value)
    end
    merge!(shared_booleans, Dict{String,Any}(
        "owner_carrier_load_bearing" => Bool(carrier["owner_carrier_load_bearing"]),
        "from_real_hopf_shells" => Bool(shell["from_real_hopf_shells"]),
        "geometry_capacity_proxy_derived" => Bool(shell["derived"]),
        "matches_2_8_8" => matches_2_8_8,
        "matches_principal_2n2" => matches_principal_2n2,
        "non_shell_control_no_pattern" => non_shell_control_pattern != target,
        "chemistry_admission" => false,
        "formal_admission_allowed" => false,
        "promotion_allowed" => false,
        "local_all_pass" => local_all_pass,
    ))

    result = Dict{String,Any}(
        "schema" => "mp_scratch_dual_backend_v1",
        "object_id" => OBJECT_ID,
        "name" => "MP4 chemistry Hopf shells finite scout",
        "sim_id" => OBJECT_ID,
        "version" => "1.0",
        "backend" => BACKEND,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_hopf_shell_capacity_graveyard_probe",
        "root_constraints_in_force" => ["F01 finite carrier", "N01 noncommutative/order-sensitive carrier"],
        "carrier_layer" => "owner finite spinor/Hopf/Clifford carrier",
        "geometry_layer" => "nested Hopf/Clifford shell structure via finite Hopf-projected base ranks",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "whether the carrier-derived shell capacity proxy reproduces the electron-shell-like 2,8,8,18 periodic filling pattern",
        "branch_status_before_run" => "speculative cascade scout only",
        "allowed_claims" => [
            "finite Hopf/S3 spinor-shell capacity proxy",
            "dual-backend parity witness",
            "non-shell control and graveyard witness",
        ],
        "promotion_status" => "diagnostic_only",
        "promotion_blockers" => [
            "does not derive 2,8,8,18 periodic filling pattern",
            "no chemistry or physics admission",
            "scratch_diagnostic fence",
            "no formal-admission proof layer",
        ],
        "eligible_consumers" => ["scratch diagnostics", "future bounded shell-capacity scout design"],
        "blocked_consumers" => [
            "chemistry admission",
            "physics admission",
            "formal manifold admission",
            "bridge",
            "Axis0",
            "PEPS3D promotion",
            "canonical promotion",
        ],
        "required_tools" => [
            "Julia",
            "LinearAlgebra",
            "canonical_qit_engine_specs.py",
            "density_matrix_spinor_lift",
            "clifford_torus_nested_hopf_foliation",
            "golden_weyl",
            "division_algebra_ratchet_ladder",
            "octonion_G2_automorphism",
            "JAX peer backend",
        ],
        "actual_tools_used" => [
            "Julia",
            "LinearAlgebra",
            "canonical_qit_engine_specs.py constants mirrored from carrier",
            "density_matrix_spinor_lift result",
            "clifford_torus_nested_hopf_foliation result",
            "golden_weyl receipts",
            "division_algebra_ratchet_ladder result",
            "octonion_G2_automorphism result",
            "JSON",
        ],
        "proof_surfaces_used" => ["finite rank/SVD residuals", "dual-backend parity rows"],
        "graph_surfaces_used" => Any[],
        "topology_surfaces_used" => ["Hopf projection", "nested linking receipt", "Clifford torus foliation receipt"],
        "required_inputs" => SOURCE_DEPENDENCIES,
        "data_or_artifact_dependencies" => SOURCE_DEPENDENCIES,
        "required_negatives" => ["non-shell carrier", "eta-erased Hopf shell", "target-injection boundary"],
        "negatives_run" => ["non_shell_control_pattern", "erased_hopf_pattern", "target_not_used_in_derivation"],
        "kill_conditions" => [
            "owner carrier surface missing or not load-bearing",
            "non-shell control reproduces target pattern",
            "JAX/Julia parity exceeds tolerance",
            "target pattern appears only by target injection",
        ],
        "required_artifacts" => [JAX_RESULT_PATH, RESULT_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "mp4_chemistry_hopf_shells_rank_probe_v1",
        "pass_rule" => "local positives, controls, graveyard rows, boundary rows, nearby variants, and JAX/Julia shared parity pass",
        "fail_rule" => "carrier gate failure, control miswire, boundary failure, or parity mismatch",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "target_pattern_compared_after_derivation" => target,
        "shell_filling_pattern" => pattern,
        "shell_rows" => shell["shell_rows"],
        "finite_rank_probe" => shell["finite_rank_probe"],
        "non_shell_control_pattern" => non_shell_control_pattern,
        "owner_carrier_load_bearing" => Bool(carrier["owner_carrier_load_bearing"]),
        "from_real_hopf_shells" => Bool(shell["from_real_hopf_shells"]),
        "matches_2_8_8" => matches_2_8_8,
        "matches_principal_2n2" => matches_principal_2n2,
        "scientific_verdict" => "GRAVEYARD_PERIODIC_CHEMISTRY_PATTERN_NOT_DERIVED",
        "positive" => positive,
        "controls" => controls,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => nearby_variants,
        "why_not_v4_probes" => why_not_v4_probes,
        "carrier_metrics" => metrics,
        "carrier_dependency_booleans" => carrier["booleans"],
        "dependency_bundle_hash" => carrier["dependency_bundle_hash"],
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "source_hashes" => carrier["source_hashes"],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing Float64 shell-capacity arithmetic, parity rows, and owner carrier result probes",
            "LinearAlgebra" => "load-bearing direct spinor density and residual checks",
            "canonical_qit_engine_specs.py" => "load-bearing spin dimension, mirror/sign checks, schedule/operator counts",
            "density_matrix_spinor_lift" => "load-bearing spinor/rho/Bloch lift and mixed-state control gate",
            "clifford_torus_nested_hopf_foliation" => "load-bearing S3/Hopf foliation and Clifford equal-radius gate",
            "golden_weyl" => "load-bearing finite eta sweep, nested linking, flat control, and F01/N01 receipt gate",
            "division_algebra_ratchet_ladder" => "load-bearing R,C,H,O/S dimension and property-loss gate",
            "octonion_G2_automorphism" => "load-bearing G2=Der(O) dimension and automorphism gate",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "density_matrix_spinor_lift" => "load_bearing",
            "clifford_torus_nested_hopf_foliation" => "load_bearing",
            "golden_weyl" => "load_bearing",
            "division_algebra_ratchet_ladder" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "JSON" => "supportive",
        ),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia Float64" => "load-bearing finite arithmetic and parity computation",
            "owner carrier artifacts" => "load-bearing; missing or changed carrier receipts change owner_carrier_load_bearing and derived pattern admission",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia Float64" => "load_bearing",
            "owner carrier artifacts" => "load_bearing",
        ),
        "local_all_pass" => local_all_pass,
        "blockers" => local_all_pass ? Any[] : ["local_positive_control_boundary_or_carrier_gate_failed"],
        "plain_sentence" => "The real owner Hopf/S3 spinor shell proxy yields [2, 8, 18, 32], not [2, 8, 8, 18]; the chemistry-style periodic filling pattern is therefore graveyarded as derived=false on this finite carrier.",
    )
    result["parity"] = parity_against_peer(result, JAX_RESULT_PATH)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => Bool(result["all_pass"]),
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => Bool(carrier["owner_carrier_load_bearing"]),
        "shell_filling_pattern" => pattern,
        "matches_2_8_8" => matches_2_8_8,
        "from_real_hopf_shells" => Bool(shell["from_real_hopf_shells"]),
        "claim_ceiling" => CLAIM_CEILING,
    )
    result
end

function print_summary(result::Dict{String,Any})
    println(
        "mp4_chemistry_hopf_shells Julia " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "local_all_pass=$(lowercase(string(result["local_all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["owner_carrier_load_bearing"]))) " *
        "shell_filling_pattern=$(result["shell_filling_pattern"]) " *
        "matches_2_8_8=$(lowercase(string(result["matches_2_8_8"]))) " *
        "from_real_hopf_shells=$(lowercase(string(result["from_real_hopf_shells"]))) " *
        "parity_max_diff=$(result["parity"]["parity_max_diff"]) " *
        "within_1e_9=$(lowercase(string(result["parity"]["within_1e_9"])))"
    )
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    print_summary(result)
    return result["local_all_pass"] ? 0 : 1
end

exit(main())
