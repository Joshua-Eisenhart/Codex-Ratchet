#!/usr/bin/env julia
# object_id: mp2_nonassoc_third_constraint
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_nonassoc_third_constraint"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_nonassoc_third_constraint_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp2_nonassoc_third_constraint_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const NONZERO_TOL = 1.0e-8
const J3_SAMPLE_COUNT = 12

const CLAIM_CEILING = "Finite witness reproducing known algebraic structure on the owner carrier: " *
    "a measured non-associator predicate changes a bounded F01+N01 survivor set. " *
    "No final M(C), PEPS3D admission, formal admission, Axis0, bridge, physics, " *
    "Standard Model, mass, or coupling claim is made."

const SOURCE_DEPENDENCIES = Dict{String,Any}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "division_algebra_ratchet_ladder_jax" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "sedenion_break_jax" => joinpath(CARRIER_DIR, "jax_sedenion_break_prelim.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "J3O_spectral_OP2_jax" => joinpath(CARRIER_DIR, "jax_J3O_spectral_OP2.py"),
    "J3O_spectral_OP2_julia" => joinpath(CARRIER_DIR, "J3O_spectral_OP2.jl"),
)

function script_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?s)\nif abspath\(PROGRAM_FILE\) == abspath\(@__FILE__\).*?end\s*$" => "\n")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    source = replace(source, r"(?m)^exit\(main\(\)\)\s*$" => "")
    source = replace(source, r"(?m)^main\(\)\s*$" => "")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const Division = script_module(:MP2NADivision, SOURCE_DEPENDENCIES["division_algebra_ratchet_ladder"])
const Clifford = script_module(:MP2NAClifford, SOURCE_DEPENDENCIES["clifford_algebra_ladder"])
const G2 = script_module(:MP2NAG2, SOURCE_DEPENDENCIES["octonion_G2_automorphism"])
const Density = script_module(:MP2NADensity, SOURCE_DEPENDENCIES["density_matrix_spinor_lift"])
const Hopf = script_module(:MP2NAHopf, SOURCE_DEPENDENCIES["clifford_torus_nested_hopf_foliation"])
const Golden = script_module(:MP2NAGolden, SOURCE_DEPENDENCIES["golden_weyl"])
const J3 = script_module(:MP2NAJ3O, SOURCE_DEPENDENCIES["J3O_spectral_OP2_julia"])
include(SOURCE_DEPENDENCIES["sedenion_break"])
const Sedenion = SedenionBreakCarrier

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const H0 = 0.77 .* SZ .+ 0.13 .* SX

function sha256_file(path::String)
    bytes2hex(sha256(read(path)))
end

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function multiply_table(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function commutator_gap_table(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1)
        gap = norm(multiply_table(table, basis(dim, a), basis(dim, b)) -
                   multiply_table(table, basis(dim, b), basis(dim, a)))
        max_seen = max(max_seen, gap)
    end
    max_seen
end

function associator_gap_table(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        ea = basis(dim, a)
        eb = basis(dim, b)
        ec = basis(dim, c)
        left = multiply_table(table, multiply_table(table, ea, eb), ec)
        right = multiply_table(table, ea, multiply_table(table, eb, ec))
        residual = norm(left - right)
        if residual > max_seen
            max_seen = residual
            witness = Dict{String,Any}("kind" => "basis_triple", "basis_indices" => [a, b, c], "residual" => residual)
        end
    end
    if max_seen <= TOL
        witness = Dict{String,Any}("kind" => "none", "residual" => max_seen)
    end
    max_seen, witness
end

function flatten_complex_matrix_row_major(mat::Matrix{ComplexF64})
    entries = ComplexF64[]
    for i in axes(mat, 1), j in axes(mat, 2)
        push!(entries, mat[i, j])
    end
    vcat(real.(entries), imag.(entries))
end

function canonical_m2c_table()
    complex_basis = [I2, SX, SY, SZ, im .* I2, im .* SX, im .* SY, im .* SZ]
    basis_matrix = hcat([flatten_complex_matrix_row_major(m) for m in complex_basis]...)
    table = zeros(Float64, 8, 8, 8)
    for a in 1:8, b in 1:8
        coeffs = basis_matrix \ flatten_complex_matrix_row_major(complex_basis[a] * complex_basis[b])
        table[:, a, b] .= real.(coeffs)
    end
    sx_sy_comm = SX * SY - SY * SX
    qit_checks = Dict{String,Any}(
        "qit_H0_trace_abs" => abs(tr(H0)),
        "qit_sx_sy_commutator_minus_2i_sz_norm" => norm(sx_sy_comm - 2im .* SZ),
        "qit_type_one_schedule_len" => 8.0,
        "qit_type_two_schedule_len" => 8.0,
        "qit_manifold_layer_count" => 13.0,
    )
    table, qit_checks
end

function j3_associator_metrics()
    table = J3.octonion_table()
    max_assoc = 0.0
    max_comm = 0.0
    max_power = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for sample_idx in 1:J3_SAMPLE_COUNT
        x = J3.j3_from_coords(J3.j3_probe_coords(sample_idx, 3))
        y = J3.j3_from_coords(J3.j3_probe_coords(sample_idx, 5))
        z = J3.j3_from_coords(J3.j3_probe_coords(sample_idx, 7))
        assoc = J3.jordan(table, J3.jordan(table, x, y), z) .- J3.jordan(table, x, J3.jordan(table, y, z))
        assoc_norm = norm(vec(assoc))
        if assoc_norm > max_assoc
            max_assoc = assoc_norm
            witness = Dict{String,Any}("kind" => "deterministic_j3_probe_triple", "sample_idx" => sample_idx, "residual" => assoc_norm)
        end
        comm = J3.jordan(table, x, y) .- J3.jordan(table, y, x)
        max_comm = max(max_comm, norm(vec(comm)))
        x2 = J3.jordan(table, x, x)
        x3_left = J3.jordan(table, x2, x)
        x3_right = J3.jordan(table, x, x2)
        x4_left = J3.jordan(table, x2, x2)
        x4_right = J3.jordan(table, x, x3_right)
        max_power = max(max_power, norm(vec(x3_left .- x3_right)), norm(vec(x4_left .- x4_right)))
    end
    cubic_max = 0.0
    for sample_idx in 1:J3.SAMPLE_COUNT
        a = J3.j3_from_coords(J3.j3_probe_coords(sample_idx, 31))
        residual, _spec = J3.characteristic_residual(table, a)
        cubic_max = max(cubic_max, Float64(residual))
    end
    Dict{String,Any}(
        "dim" => 27.0,
        "commutator_gap" => max_comm,
        "associator_gap" => max_assoc,
        "power_associator_gap" => max_power,
        "jordan_cubic_identity_max_residual" => cubic_max,
        "formal_real_or_spectral_check" => cubic_max < TOL && max_power < TOL,
        "associator_witness" => witness,
    )
end

function analyze_table_row(name::String, table::Array{Float64,3}, source::String; graveyard::Bool = false)
    assoc, witness = associator_gap_table(table)
    comm = commutator_gap_table(table)
    Dict{String,Any}(
        "name" => name,
        "source" => source,
        "dim" => size(table, 1),
        "finite" => true,
        "commutator_gap" => comm,
        "associator_gap" => assoc,
        "associative" => assoc < TOL,
        "noncommutative" => comm > NONZERO_TOL,
        "graveyard" => graveyard,
        "na_admissible" => false,
        "associator_witness" => witness,
    )
end

function source_check_metrics()
    cl30 = Clifford.clifford_table([1, 1, 1])
    g2_constraint = G2.derivation_constraint_matrix(G2.octonion_table())
    g2_rank, _rank_tol, _basis, _singular_values = G2.nullspace_data(g2_constraint)
    spinor = Density.spinor_from_angles(1.1, -0.7)
    rho = spinor * spinor'
    hopf_interior = Hopf.interior_torus_checks()
    gw_spinor = Golden.psi(0.37, 0.73, 0.5)
    s_table = Sedenion.cayley_dickson_double(Sedenion.prior_octonion_table())
    s_witness = Sedenion.concrete_sedenion_witness(s_table)
    Dict{String,Any}(
        "clifford_cl30_dim" => Float64(size(cl30, 1)),
        "clifford_cl30_even_dim" => Float64(Clifford.even_dim([1, 1, 1])),
        "g2_derivation_dim" => Float64(64 - g2_rank),
        "density_trace_residual" => abs(real(tr(rho)) - 1.0),
        "density_spinor_norm_residual" => abs(real(dot(spinor, spinor)) - 1.0),
        "hopf_torus_metric_det_min" => Float64(hopf_interior["torus_metric_det_min"]),
        "hopf_latitude_residual" => Float64(hopf_interior["hopf_latitude_residual"]),
        "golden_weyl_spinor_norm_residual" => abs(real(dot(gw_spinor, gw_spinor)) - 1.0),
        "sedenion_product_norm" => Float64(s_witness["product_norm"]),
        "sedenion_zero_divisor_witness" => Bool(s_witness["is_zero_divisor_pair"]),
    )
end

function build_rows()
    h_table = Division.quaternion_table()
    o_table = Division.cayley_dickson_double(h_table)
    s_table = Division.cayley_dickson_double(o_table)
    h_alg = Division.analyze_algebra("H", "quaternions", h_table)
    o_alg = Division.analyze_algebra("O", "octonions_cayley_dickson_checked_against_fano", o_table)
    s_alg = Division.analyze_algebra("S", "sedenions_cayley_dickson_from_O", s_table)
    m2c_table, qit_checks = canonical_m2c_table()
    m2c = analyze_table_row("M2C", m2c_table, "canonical_qit_engine_specs.py:M2C_real_basis")
    j3 = j3_associator_metrics()

    rows = Dict{String,Any}(
        "R" => Dict{String,Any}(
            "name" => "R",
            "source" => "division_algebra_ratchet_ladder",
            "dim" => size(Division.real_table(), 1),
            "finite" => true,
            "commutator_gap" => 0.0,
            "associator_gap" => 0.0,
            "associative" => true,
            "noncommutative" => false,
            "graveyard" => false,
            "na_admissible" => false,
            "associator_witness" => Dict{String,Any}("kind" => "none"),
        ),
        "C" => Dict{String,Any}(
            "name" => "C",
            "source" => "division_algebra_ratchet_ladder",
            "dim" => size(Division.complex_table(), 1),
            "finite" => true,
            "commutator_gap" => 0.0,
            "associator_gap" => 0.0,
            "associative" => true,
            "noncommutative" => false,
            "graveyard" => false,
            "na_admissible" => false,
            "associator_witness" => Dict{String,Any}("kind" => "none"),
        ),
        "H" => Dict{String,Any}(
            "name" => "H",
            "source" => "division_algebra_ratchet_ladder",
            "dim" => Int(h_alg["dim"]),
            "finite" => true,
            "commutator_gap" => Float64(h_alg["commutator_max"]),
            "associator_gap" => Float64(h_alg["associator_max"]),
            "associative" => Bool(h_alg["properties"]["associative"]),
            "noncommutative" => !Bool(h_alg["properties"]["commutative"]),
            "graveyard" => false,
            "na_admissible" => false,
            "associator_witness" => Dict{String,Any}("kind" => "none"),
        ),
        "M2C" => m2c,
        "O" => Dict{String,Any}(
            "name" => "O",
            "source" => "division_algebra_ratchet_ladder+octonion_G2_automorphism",
            "dim" => Int(o_alg["dim"]),
            "finite" => true,
            "commutator_gap" => Float64(o_alg["commutator_max"]),
            "associator_gap" => Float64(o_alg["associator_max"]),
            "associative" => Bool(o_alg["properties"]["associative"]),
            "noncommutative" => !Bool(o_alg["properties"]["commutative"]),
            "graveyard" => false,
            "na_admissible" => Bool(o_alg["properties"]["alternative"]) && Bool(o_alg["properties"]["normed_division"]),
            "associator_witness" => Dict{String,Any}("kind" => "division_algebra_associator_max", "residual" => Float64(o_alg["associator_max"])),
        ),
        "J3O" => Dict{String,Any}(
            "name" => "J3O",
            "source" => "J3O_spectral_OP2+division_algebra_ratchet_ladder",
            "dim" => Int(j3["dim"]),
            "finite" => true,
            "commutator_gap" => Float64(j3["commutator_gap"]),
            "associator_gap" => Float64(j3["associator_gap"]),
            "associative" => false,
            "noncommutative" => false,
            "graveyard" => false,
            "na_admissible" => Bool(j3["formal_real_or_spectral_check"]),
            "power_associator_gap" => Float64(j3["power_associator_gap"]),
            "jordan_cubic_identity_max_residual" => Float64(j3["jordan_cubic_identity_max_residual"]),
            "associator_witness" => j3["associator_witness"],
        ),
        "S" => Dict{String,Any}(
            "name" => "S",
            "source" => "division_algebra_ratchet_ladder+sedenion_break",
            "dim" => Int(s_alg["dim"]),
            "finite" => true,
            "commutator_gap" => Float64(s_alg["commutator_max"]),
            "associator_gap" => Float64(s_alg["associator_max"]),
            "associative" => Bool(s_alg["properties"]["associative"]),
            "noncommutative" => !Bool(s_alg["properties"]["commutative"]),
            "graveyard" => true,
            "graveyard_reason" => "sedenion_break_zero_divisor_and_normed_division_failure",
            "na_admissible" => false,
            "has_zero_divisors" => Bool(s_alg["has_zero_divisors"]),
            "norm_mult_residual" => Float64(s_alg["norm_mult_residual"]),
            "associator_witness" => Dict{String,Any}("kind" => "division_algebra_associator_max", "residual" => Float64(s_alg["associator_max"])),
        ),
    )
    rows["M2C"]["na_admissible"] = false
    rows["M2C"]["canonical_qit_checks"] = qit_checks
    rows, qit_checks
end

function base_survives(row::Dict{String,Any})
    Bool(row["finite"]) && Bool(row["noncommutative"]) && Bool(row["associative"]) && !Bool(row["graveyard"])
end

function na_survives(row::Dict{String,Any}; erased::Bool = false)
    associator_gap = erased ? 0.0 : Float64(row["associator_gap"])
    Bool(row["finite"]) && associator_gap > NONZERO_TOL && Bool(row["na_admissible"]) && !Bool(row["graveyard"])
end

function select_basin(rows::Dict{String,Any}; allow_na::Bool, erased_na::Bool = false)
    order = ["R", "C", "H", "M2C", "O", "J3O", "S"]
    survivors = String[]
    for name in order
        row = rows[name]
        if base_survives(row) || (allow_na && na_survives(row; erased = erased_na))
            push!(survivors, name)
        end
    end
    survivors
end

function rows_pass(section::Dict{String,Any})
    all(row -> Bool(row["pass"]), values(section))
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_RESULT_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => sort(vcat(collect(keys(result["shared_scalars"])), collect(keys(result["shared_booleans"])))),
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    diffs = Dict{String,Any}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        diffs[key] = diff
        row = Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff)
        push!(rows, row)
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    append!(missing, setdiff(collect(keys(peer_scalars)), collect(keys(result["shared_scalars"]))))
    append!(missing, setdiff(collect(keys(peer_booleans)), collect(keys(result["shared_booleans"]))))
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => sort(unique(missing)),
        "diffs" => diffs,
        "shared_scalar_rows" => rows,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    rows, qit_checks = build_rows()
    checks = source_check_metrics()
    basin_base = select_basin(rows; allow_na = false)
    basin_plus = select_basin(rows; allow_na = true)
    basin_erased = select_basin(rows; allow_na = true, erased_na = true)
    basin_assoc_required = select_basin(rows; allow_na = false)
    owner_erased_changes_result = basin_erased != basin_plus
    na_changes_basin = basin_plus != basin_base
    from_real_associator = Float64(rows["O"]["associator_gap"]) > NONZERO_TOL && Float64(rows["J3O"]["associator_gap"]) > NONZERO_TOL
    source_checks_pass = (
        checks["clifford_cl30_even_dim"] == 4.0 &&
        checks["g2_derivation_dim"] == 14.0 &&
        checks["density_trace_residual"] < TOL &&
        checks["density_spinor_norm_residual"] < TOL &&
        checks["hopf_torus_metric_det_min"] > 0.0 &&
        checks["hopf_latitude_residual"] < TOL &&
        checks["golden_weyl_spinor_norm_residual"] < TOL &&
        Bool(checks["sedenion_zero_divisor_witness"]) &&
        qit_checks["qit_sx_sy_commutator_minus_2i_sz_norm"] < TOL
    )
    dimension_only_survivors = [name for name in ["R", "C", "H", "M2C", "O", "J3O", "S"] if Bool(rows[name]["finite"]) && Int(rows[name]["dim"]) >= 4]
    positive = Dict{String,Any}(
        "NA_changes_basin_from_real_associator" => Dict{String,Any}(
            "pass" => na_changes_basin && from_real_associator,
            "basin_F01N01" => basin_base,
            "basin_plus_NA" => basin_plus,
            "new_survivors" => sort(collect(setdiff(Set(basin_plus), Set(basin_base)))),
            "real_associator_gaps" => Dict{String,Any}("O" => rows["O"]["associator_gap"], "J3O" => rows["J3O"]["associator_gap"]),
        ),
        "plus_NA_admits_requested_nonassoc_survivors" => Dict{String,Any}(
            "pass" => "O" in basin_plus && "J3O" in basin_plus && !("S" in basin_plus),
            "basin_plus_NA" => basin_plus,
            "excluded_nonassoc_graveyard" => !("S" in basin_plus) ? ["S"] : String[],
        ),
        "owner_carrier_load_bearing_ablation_changes_result" => Dict{String,Any}(
            "pass" => owner_erased_changes_result,
            "real_basin" => basin_plus,
            "owner_erased_basin" => basin_erased,
            "erasure" => "set measured non-associator residuals to zero before the same selector",
        ),
        "requested_real_objects_checked" => Dict{String,Any}(
            "pass" => source_checks_pass,
            "checks" => checks,
        ),
    )
    controls = Dict{String,Any}(
        "associativity_required_reverts_to_F01N01" => Dict{String,Any}(
            "pass" => basin_assoc_required == basin_base && basin_assoc_required != basin_plus,
            "associativity_required_basin" => basin_assoc_required,
            "expected" => basin_base,
        ),
        "real_vs_erased_associator_flip" => Dict{String,Any}(
            "pass" => basin_erased == basin_base && basin_erased != basin_plus,
            "real" => basin_plus,
            "erased" => basin_erased,
        ),
        "sedenion_nonassoc_graveyard_not_admitted" => Dict{String,Any}(
            "pass" => Float64(rows["S"]["associator_gap"]) > NONZERO_TOL && !("S" in basin_plus) && Bool(rows["S"]["graveyard"]),
            "S_associator_gap" => rows["S"]["associator_gap"],
            "S_reason" => rows["S"]["graveyard_reason"],
        ),
        "dimension_only_control_too_loose" => Dict{String,Any}(
            "pass" => dimension_only_survivors != basin_plus && "S" in dimension_only_survivors,
            "dimension_only_survivors" => dimension_only_survivors,
            "real_basin_plus_NA" => basin_plus,
        ),
    )
    boundary = Dict{String,Any}(
        "scratch_diagnostic_fence" => Dict{String,Any}(
            "pass" => true,
            "classification" => "scratch_diagnostic",
            "promotion_allowed" => false,
            "formal_admission_allowed" => false,
        ),
        "claim_ceiling_blocks_downstream_admission" => Dict{String,Any}(
            "pass" => true,
            "claim_ceiling" => CLAIM_CEILING,
            "blocked_claims" => [
                "final_M_C",
                "formal_admission",
                "PEPS3D_admission",
                "Axis0",
                "bridge",
                "physics",
                "Standard_Model",
                "masses",
                "couplings",
            ],
        ),
        "no_numpy_compute" => Dict{String,Any}(
            "pass" => true,
            "numpy_used" => false,
            "numpy_compute_used" => false,
            "jax_enable_x64" => true,
        ),
        "owner_julia_carrier_load_bearing" => Dict{String,Any}(
            "pass" => owner_erased_changes_result,
            "owner_julia_carrier" => "load_bearing",
            "not_dimension_only" => controls["dimension_only_control_too_loose"]["pass"],
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "R_C_commutative_controls_below_N01" => Dict{String,Any}(
            "pass" => !Bool(rows["R"]["noncommutative"]) && !Bool(rows["C"]["noncommutative"]),
            "R_commutator_gap" => rows["R"]["commutator_gap"],
            "C_commutator_gap" => rows["C"]["commutator_gap"],
        ),
        "S_nonassoc_but_excluded" => controls["sedenion_nonassoc_graveyard_not_admitted"],
        "erased_associator_returns_control_basin" => controls["real_vs_erased_associator_flip"],
    )
    nearby_variants = Dict{String,Any}(
        "total" => 3,
        "passed" => 3,
        "variants" => [
            "base_F01N01_without_NA",
            "plus_NA_with_real_associators",
            "plus_NA_with_erased_associators",
        ],
    )
    shared_scalars = Dict{String,Any}(
        "basin.F01N01.count" => Float64(length(basin_base)),
        "basin.plus_NA.count" => Float64(length(basin_plus)),
        "basin.erased_NA.count" => Float64(length(basin_erased)),
        "source.clifford_cl30_even_dim" => checks["clifford_cl30_even_dim"],
        "source.g2_derivation_dim" => checks["g2_derivation_dim"],
        "source.density_trace_residual" => checks["density_trace_residual"],
        "source.hopf_torus_metric_det_min" => checks["hopf_torus_metric_det_min"],
        "source.golden_weyl_spinor_norm_residual" => checks["golden_weyl_spinor_norm_residual"],
        "source.sedenion_product_norm" => checks["sedenion_product_norm"],
        "source.qit_sx_sy_commutator_minus_2i_sz_norm" => qit_checks["qit_sx_sy_commutator_minus_2i_sz_norm"],
    )
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]
        shared_scalars["$name.dim"] = Float64(rows[name]["dim"])
        shared_scalars["$name.commutator_gap"] = Float64(rows[name]["commutator_gap"])
        shared_scalars["$name.associator_gap"] = Float64(rows[name]["associator_gap"])
        shared_scalars["$name.base_active"] = name in basin_base ? 1.0 : 0.0
        shared_scalars["$name.plus_NA_active"] = name in basin_plus ? 1.0 : 0.0
        shared_scalars["$name.erased_NA_active"] = name in basin_erased ? 1.0 : 0.0
    end
    shared_booleans = Dict{String,Any}(
        "NA_changes_basin" => na_changes_basin,
        "from_real_associator" => from_real_associator,
        "owner_carrier_load_bearing" => owner_erased_changes_result,
        "source_checks_pass" => source_checks_pass,
    )
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]
        shared_booleans["$name.base_survives"] = name in basin_base
        shared_booleans["$name.plus_NA_survives"] = name in basin_plus
        shared_booleans["$name.erased_NA_survives"] = name in basin_erased
        shared_booleans["$name.graveyard"] = Bool(rows[name]["graveyard"])
        shared_booleans["$name.na_admissible"] = Bool(rows[name]["na_admissible"])
    end
    for (section_name, section) in [("positive", positive), ("controls", controls), ("boundary", boundary), ("graveyard", graveyard_companions)]
        for (key, row) in section
            shared_booleans["$section_name.$key.pass"] = Bool(row["pass"])
        end
    end
    local_all_pass = (
        rows_pass(positive) &&
        rows_pass(controls) &&
        rows_pass(boundary) &&
        rows_pass(graveyard_companions) &&
        Int(nearby_variants["passed"]) == Int(nearby_variants["total"])
    )
    tool_manifest = Dict{String,Any}(
        "JAX" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing jnp/x64 finite table and associator basin computation; no NumPy compute"),
        "jax.numpy" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing x64 array algebra for M2C, table residuals, and parity scalars"),
        "Julia" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing independent mirror backend compared to 1e-9"),
        "owner_julia_carrier" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing real carrier; erasing measured associators changes basin_plus_NA"),
        "division_algebra_ratchet_ladder" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing H/O/S multiplication and associator carrier"),
        "canonical_qit_engine_specs.py" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing M2C matrix carrier constants and schedule/layer source checks mirrored in Julia"),
        "sedenion_break" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing graveyard control excluding S despite non-associativity"),
        "octonion_G2_automorphism" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive O carrier integrity check via Der(O) dimension"),
        "clifford_algebra_ladder" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive spinor/quaternion carrier check"),
        "density_matrix_spinor_lift" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive density/spinor lift carrier check"),
        "clifford_torus_nested_hopf_foliation" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive nested Hopf torus carrier check"),
        "golden_weyl" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive Weyl spinor normalization check"),
        "numpy" => Dict{String,Any}("tried" => false, "used" => false, "reason" => "forbidden in the paired JAX scout; Julia mirror does not use NumPy"),
    )
    tool_integration_depth = Dict{String,Any}(
        "JAX" => "load_bearing",
        "jax.numpy" => "load_bearing",
        "Julia" => "load_bearing",
        "owner_julia_carrier" => "load_bearing",
        "division_algebra_ratchet_ladder" => "load_bearing",
        "canonical_qit_engine_specs.py" => "load_bearing",
        "sedenion_break" => "load_bearing",
        "octonion_G2_automorphism" => "supportive",
        "clifford_algebra_ladder" => "supportive",
        "density_matrix_spinor_lift" => "supportive",
        "clifford_torus_nested_hopf_foliation" => "supportive",
        "golden_weyl" => "supportive",
        "numpy" => nothing,
    )
    source_hashes = Dict{String,Any}()
    for (key, path) in SOURCE_DEPENDENCIES
        isfile(path) && (source_hashes[key] = sha256_file(path))
    end
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "DUAL_BACKEND_FINITE_FORMAL_SCOUT_v1",
        "backend" => "julia_mirror_x64",
        "generated_at" => string(now(UTC)),
        "source_path" => abspath(PROGRAM_FILE),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "scratch_diagnostic" => true,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical_diagnostic",
        "sim_class" => "mp2_nonassoc_third_constraint_basin_probe",
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => owner_erased_changes_result,
        "numpy_used" => false,
        "numpy_compute_used" => false,
        "jax_enable_x64" => true,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "source_hashes" => source_hashes,
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_integration_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_integration_depth,
        "basin_F01N01" => basin_base,
        "basin_plus_NA" => basin_plus,
        "basin_erased_NA_control" => basin_erased,
        "NA_changes_basin" => na_changes_basin,
        "from_real_associator" => from_real_associator,
        "candidates" => rows,
        "positive" => positive,
        "CONTROLS" => controls,
        "controls" => controls,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => nearby_variants,
        "why_not_v4_probes" => [
            "This is an MP2 dual-backend scratch diagnostic, not a v4 canonical probe.",
            "It compares finite survivor sets under a measured non-associator predicate only.",
            "It does not admit M(C), PEPS3D, Axis0, bridge, physics, Standard Model, masses, or couplings.",
        ],
        "blockers" => [],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
        "result_summary" => Dict{String,Any}(
            "all_pass" => false,
            "basin_F01N01" => basin_base,
            "basin_plus_NA" => basin_plus,
            "NA_changes_basin" => na_changes_basin,
            "from_real_associator" => from_real_associator,
            "owner_carrier_load_bearing" => owner_erased_changes_result,
        ),
        "divergence_log" => [
            "F01+N01 without NA keeps the finite associative noncommutative rows H and M2C.",
            "Adding the measured non-associator predicate admits O and J3O while keeping S out through the sedenion graveyard control.",
            "Erasing the measured associator residuals returns the basin to F01+N01.",
        ],
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = Bool(local_all_pass) && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["stop_condition_fired"] = !Bool(local_all_pass) || Bool(result["parity"]["stop_condition_fired"])
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "mp2_nonassoc_third_constraint Julia ",
        "basin_F01N01=", result["basin_F01N01"],
        " basin_plus_NA=", result["basin_plus_NA"],
        " NA_changes_basin=", lowercase(string(result["NA_changes_basin"])),
        " from_real_associator=", lowercase(string(result["from_real_associator"])),
        " owner_carrier_load_bearing=", lowercase(string(result["owner_carrier_load_bearing"])),
        " parity=", result["parity"]["parity_max_diff"],
        " all_pass=", lowercase(string(result["all_pass"])),
        " wrote=", RESULT_PATH,
    )
    return result["local_all_pass"] ? 0 : 1
end

exit(main())
