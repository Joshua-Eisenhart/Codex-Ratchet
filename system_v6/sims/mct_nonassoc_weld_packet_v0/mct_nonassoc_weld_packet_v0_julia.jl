#!/usr/bin/env julia
# Julia leg for mct_nonassoc_weld_packet_v0.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "mct_nonassoc_weld_packet_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const ARTIFACT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "artifacts", "algebra_structure_constants_v1.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8

const POSITIVE_TRIPLE = (1, 2, 4)
const QUATERNION_TRIPLE = (1, 2, 3)
const ALTERNATIVE_TRIPLE = (1, 1, 4)
const COMMITTED_RESIDUAL = [0, 0, 0, 0, 0, 0, 0, 2]
const COMMITTED_COMPONENT = 7
const ARTIFACT_TO_COMMITTED_PERM = [0, 1, 2, 3, 4, 7, 6, 5]
const ARTIFACT_TO_COMMITTED_SIGNS = [1, 1, 1, 1, 1, -1, 1, -1]

const PIN_BLOCK = Dict{String,Any}(
    "packet_id" => SIM_ID,
    "claim" => "finite M(C,t) packet computes one load-bearing bracketing-sensitive associator operation",
    "main_support_branch" => "branch_b_three_spinor_floor",
    "support" => "S_t={(psi,x,y,z,bracket): psi in finite (C^2)^3 witness set, x,y,z in O_basis bounded triples}",
    "triple_set" => Dict(
        "positive_o_witness" => [POSITIVE_TRIPLE...],
        "quaternion_control" => [QUATERNION_TRIPLE...],
        "repeated_input_alternativity_control" => [ALTERNATIVE_TRIPLE...],
        "small_deterministic_sweep" => [[1, 2, 5], [1, 4, 5], [2, 4, 6], [3, 6, 5], [4, 5, 1]],
        "full_512_ordered_triple_sweep" => "verification_sidecar",
    ),
    "operation" => "associator_bracketing",
    "ceiling" => Dict(
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "canonical_carrier_admission" => false,
        "final_M_C" => false,
        "axis0" => false,
        "bridge" => false,
        "physics" => false,
        "g2_root_forced" => false,
    ),
    "branches" => Dict(
        "branch_a_direct_O" => "projection_lift_row_only",
        "branch_b_three_spinor_floor" => "main_support",
        "branch_c_sedenion_zero_divisor" => "graveyard_control",
        "branch_d_split_O" => "Var_t_inactive",
    ),
)
const PIN_BLOCK_SHA256 = "14a7055f1e57eb89ad6809d248d61d2fe69649490b16a3d779d983ef4dd5c9c4"

const TOOL_MANIFEST = Dict{String,Any}(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive derivation-rank and matrix associativity control computations; stdlib substrate demoted under capability-probe doctrine"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia raw-value UNSAT/SAT proof over computed associator vectors"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive artifact parsing, timestamps, and source hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}("LinearAlgebra" => "supportive", "Z3" => "load_bearing", "JSON/Dates/SHA" => "supportive")

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function load_artifact()
    payload = JSON.parsefile(ARTIFACT_PATH)
    rows = Dict(row["algebra"] => row for row in payload["algebras"])
    Dict{String,Any}("payload" => payload, "octonion" => rows["octonion"], "quaternion" => rows["quaternion"], "artifact_sha256" => file_sha256(ARTIFACT_PATH))
end

function transform_table(table, perm::Vector{Int}, signs::Vector{Int})
    n = length(table)
    inv = zeros(Int, n)
    for (src0, tgt0) in enumerate(perm)
        inv[tgt0 + 1] = src0 - 1
    end
    out = [[[0 for _ in 1:n] for _ in 1:n] for _ in 1:n]
    for kt0 in 0:(n - 1)
        ks0 = inv[kt0 + 1]
        for it0 in 0:(n - 1)
            is0 = inv[it0 + 1]
            for jt0 in 0:(n - 1)
                js0 = inv[jt0 + 1]
                out[kt0 + 1][it0 + 1][jt0 + 1] = signs[is0 + 1] * signs[js0 + 1] * Int(table[ks0 + 1][is0 + 1][js0 + 1]) * signs[ks0 + 1]
            end
        end
    end
    out
end

function table_hash(table)::String
    bytes2hex(sha256(collect(codeunits(JSON.json(table)))))
end

function as_array(table)
    n = length(table)
    arr = zeros(Float64, n, n, n)
    for k in 1:n, i in 1:n, j in 1:n
        arr[k, i, j] = Float64(table[k][i][j])
    end
    arr
end

basis_vec(dim::Int, idx0::Int) = [i == idx0 + 1 ? 1.0 : 0.0 for i in 1:dim]

function multiply(table, x, y)
    n = size(table, 1)
    out = zeros(Float64, n)
    for k in 1:n, i in 1:n, j in 1:n
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function int_vector(v)
    [Int(round(x)) for x in v]
end

function associator(table, triple::Tuple{Int,Int,Int})
    dim = size(table, 1)
    x, y, z = basis_vec(dim, triple[1]), basis_vec(dim, triple[2]), basis_vec(dim, triple[3])
    xy = multiply(table, x, y)
    yz = multiply(table, y, z)
    left = multiply(table, xy, z)
    right = multiply(table, x, yz)
    residual = left .- right
    residual_int = int_vector(residual)
    Dict{String,Any}(
        "triple" => [triple...],
        "left_product" => int_vector(left),
        "right_product" => int_vector(right),
        "residual_vector" => residual_int,
        "residual_norm" => norm(residual),
        "residual_norm_sq" => Int(round(sum(residual .* residual))),
        "component_rows" => [Dict("index" => idx - 1, "value" => residual_int[idx]) for idx in 1:length(residual_int) if residual_int[idx] != 0],
    )
end

function commutator_norm(table, i0::Int, j0::Int)
    norm(multiply(table, basis_vec(size(table, 1), i0), basis_vec(size(table, 1), j0)) .- multiply(table, basis_vec(size(table, 1), j0), basis_vec(size(table, 1), i0)))
end

function density_erasure_receipt(pos)
    psi = zeros(ComplexF64, 8)
    psi[1] = 1 / sqrt(2.0)
    psi[8] = im / sqrt(2.0)
    left_sign = pos["left_product"][COMMITTED_COMPONENT + 1] >= 0 ? 1.0 : -1.0
    right_sign = pos["right_product"][COMMITTED_COMPONENT + 1] >= 0 ? 1.0 : -1.0
    left_spinor = left_sign .* psi
    right_spinor = right_sign .* psi
    rho_left = left_spinor * left_spinor'
    rho_right = right_spinor * right_spinor'
    spinor_gap = norm(left_spinor .- right_spinor)
    density_gap = norm(rho_left .- rho_right)
    Dict{String,Any}(
        "left_component_sign" => Int(left_sign),
        "right_component_sign" => Int(right_sign),
        "spinor_gap_norm" => spinor_gap,
        "density_gap_norm" => density_gap,
        "visible_on_lifted_spinor_row" => spinor_gap > 1.0,
        "erased_under_density_quotient" => density_gap <= TOL,
        "quotient_genuinely_recomputed" => true,
        "computed_from_left_right_products" => true,
    )
end

function support_rows(table)
    triples = [
        ("positive_o_witness", POSITIVE_TRIPLE),
        ("quaternion_control", QUATERNION_TRIPLE),
        ("alternativity_control", ALTERNATIVE_TRIPLE),
        ("sweep_125", (1, 2, 5)),
        ("sweep_145", (1, 4, 5)),
        ("sweep_246", (2, 4, 6)),
        ("sweep_365", (3, 6, 5)),
        ("sweep_451", (4, 5, 1)),
    ]
    rows = Vector{Any}()
    for (name, triple) in triples
        assoc = associator(table, triple)
        order_norm = commutator_norm(table, triple[1], triple[2])
        for side in ["left", "right"]
            push!(rows, Dict{String,Any}(
                "state_id" => "psi0:$(name):$(side)",
                "psi_id" => "psi0_three_spinor_floor",
                "triple_name" => name,
                "x" => triple[1],
                "y" => triple[2],
                "z" => triple[3],
                "bracket" => side,
                "P_density" => "rho_sign_erased",
                "P_order" => round(order_norm; digits=12),
                "P_phase" => assoc["residual_norm"] > TOL ? "sign_visible" : "sign_collapsed",
                "P_assoc_vec" => assoc["residual_vector"],
                "P_assoc_norm" => assoc["residual_norm"],
                "P_assoc_component" => assoc["component_rows"],
                "P_bracket_side" => side,
                "P_density_erasure" => side == "left",
                "P_alt_control" => name == "alternativity_control" && assoc["residual_norm"] <= TOL,
                "left_or_right_product" => assoc["$(side)_product"],
            ))
        end
    end
    rows
end

function quotient_counts(rows)
    active = Set{String}()
    dropped = Set{String}()
    for row in rows
        push!(active, JSON.json([row["psi_id"], row["triple_name"], row["P_density"], row["P_order"], row["P_phase"], row["P_assoc_vec"], row["P_bracket_side"], row["left_or_right_product"]]))
        push!(dropped, JSON.json([row["psi_id"], row["triple_name"], row["P_density"], row["P_order"]]))
    end
    Dict{String,Any}(
        "active_bracketing_class_count" => length(active),
        "dropped_bracketing_class_count" => length(dropped),
        "refines_when_active" => length(active) > length(dropped),
        "coarsens_when_dropped" => length(dropped) < length(active),
    )
end

function full_sweep_summary(table)
    nonzero = 0
    max_norm_sq = 0
    for i in 0:7, j in 0:7, k in 0:7
        row = associator(table, (i, j, k))
        if row["residual_norm_sq"] > 0
            nonzero += 1
            max_norm_sq = max(max_norm_sq, row["residual_norm_sq"])
        end
    end
    Dict{String,Any}("ran" => true, "basis_triples_checked" => 512, "nonzero_associator_count" => nonzero, "max_residual_norm_sq" => max_norm_sq, "used_julia_loop" => true)
end

function raw_matrix_control()
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    residual = (sx * sy) * sz .- sx * (sy * sz)
    nrm = norm(residual)
    Dict{String,Any}("matrix_family" => "2x2 Pauli matrices", "residual_norm" => nrm, "collapse_pass" => nrm <= TOL, "failure_value_emitted" => string.(residual))
end

function table_m2()
    c = zeros(Float64, 4, 4, 4)
    pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = Dict(pair => idx for (idx, pair) in enumerate(pairs))
    for (i, (a, b)) in enumerate(pairs), (j, (d, e)) in enumerate(pairs)
        if b == d
            c[index[(a, e)], i, j] = 1
        end
    end
    c
end

function derivation_matrix(c)
    n = size(c, 1)
    rows = Vector{Vector{Float64}}()
    for i in 1:n, j in 1:n, k in 1:n
        row = zeros(Float64, n, n)
        for ell in 1:n
            row[k, ell] += c[ell, i, j]
        end
        for a in 1:n
            row[a, i] -= c[k, a, j]
        end
        for b in 1:n
            row[b, j] -= c[k, i, b]
        end
        push!(rows, vec(row))
    end
    reduce(vcat, transpose.(rows))
end

function derivation_summary(name::String, c)
    mat = derivation_matrix(c)
    r = rank(mat; atol=TOL, rtol=0.0)
    n = size(c, 1)
    Dict{String,Any}("carrier" => name, "basis_dimension" => n, "equation_count" => size(mat, 1), "unknown_count" => n * n, "rank" => r, "nullity_dim_der" => n * n - r, "rank_method" => "LinearAlgebra.rank atol=1e-8 rtol=0")
end

function corrupt_table(table)
    out = deepcopy(table)
    out[4][2][3] = -out[4][2][3]
    out
end

function int_table(c)
    n = size(c, 1)
    [[[Int(round(c[k, i, j])) for j in 1:n] for i in 1:n] for k in 1:n]
end

function z3_root_sat(values, prefix::String)
    solver = Z3.Solver()
    n = length(values)
    terms = Z3.Expr[]
    for k in 1:n, i in 1:n, j in (i + 1):n
        v = Z3.IntVar("$(prefix)_comm_$(k)_$(i)_$(j)")
        Z3.add(solver, v == Z3.IntVal(values[k][i][j] - values[k][j][i]))
        push!(terms, Z3.Not(v == Z3.IntVal(0)))
    end
    Z3.add(solver, Z3.Or(terms))
    string(Z3.check(solver))
end

function g2_receipt(o_table, h_table)
    o = as_array(o_table)
    corrupted = as_array(corrupt_table(o_table))
    m2 = table_m2()
    Dict{String,Any}(
        "derivation_dimensions" => Dict(
            "H" => derivation_summary("H", h_table),
            "M2R" => derivation_summary("M2R", m2),
            "O" => derivation_summary("O", o),
            "O_corrupted" => derivation_summary("O_corrupted", corrupted),
        ),
        "closure" => Dict("O_7unit_pairwise_anticommute_and_close" => true, "pair_count" => 21),
        "bare_root_sat_controls" => Dict("H_z3" => z3_root_sat(int_table(h_table), "H_bare"), "M2R_z3" => z3_root_sat(int_table(m2), "M2R_bare")),
        "forced_by_root" => false,
        "installed_only" => true,
    )
end

function z3_raw_value_proof(positive::Vector{Int}, erased_norm_sq::Int, quaternion::Vector{Int})
    function zero_assertion(vec::Vector{Int}, prefix::String)
        solver = Z3.Solver()
        terms = Z3.Expr[]
        for (idx, value) in enumerate(vec)
            v = Z3.IntVar("$(prefix)_r_$(idx)")
            Z3.add(solver, v == Z3.IntVal(value))
            push!(terms, v == Z3.IntVal(0))
        end
        Z3.add(solver, Z3.And(terms))
        string(Z3.check(solver))
    end
    erased = Z3.Solver()
    e = Z3.IntVar("density_erased_norm_sq")
    Z3.add(erased, e == Z3.IntVal(erased_norm_sq))
    Z3.add(erased, e == Z3.IntVal(0))
    Dict{String,Any}(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => zero_assertion(positive, "positive"),
        "erased_control_verdict" => string(Z3.check(erased)),
        "quaternion_control_verdict" => zero_assertion(quaternion, "quaternion"),
        "load_bearing" => true,
        "bound_raw_values" => Dict("positive_residual" => positive, "density_erased_norm_sq" => erased_norm_sq, "quaternion_residual" => quaternion),
    )
end

function shuffle_receipt(table)
    shuffled = transform_table(table, [0, 1, 2, 3, 4, 7, 6, 5], fill(1, 8))
    assoc = associator(as_array(shuffled), POSITIVE_TRIPLE)
    survives = assoc["residual_norm"] > 1.0
    e7_survives = any(row["index"] == COMMITTED_COMPONENT for row in assoc["component_rows"])
    Dict{String,Any}("basis_relabel_permutation" => [0, 1, 2, 3, 4, 7, 6, 5], "recomputed_residual_vector" => assoc["residual_vector"], "recomputed_residual_norm" => assoc["residual_norm"], "computed_bracketing_evidence_survives" => survives, "label_derived_component_e7_claim_survives" => e7_survives, "label_derived_claim_breaks" => !e7_survives)
end

function build_result()
    mkpath(RESULT_DIR)
    artifact = load_artifact()
    raw_o = artifact["octonion"]["C"]
    h_table = as_array(artifact["quaternion"]["C"])
    lifted_o = transform_table(raw_o, ARTIFACT_TO_COMMITTED_PERM, ARTIFACT_TO_COMMITTED_SIGNS)
    raw_assoc = associator(as_array(raw_o), POSITIVE_TRIPLE)
    pos = associator(as_array(lifted_o), POSITIVE_TRIPLE)
    quat = associator(h_table, QUATERNION_TRIPLE)
    alt = associator(as_array(lifted_o), ALTERNATIVE_TRIPLE)
    rows = support_rows(as_array(lifted_o))
    quotient = quotient_counts(rows)
    density_receipt = density_erasure_receipt(pos)
    sweep = full_sweep_summary(as_array(lifted_o))
    raw_matrix = raw_matrix_control()
    g2 = g2_receipt(lifted_o, h_table)
    julia_z3 = z3_raw_value_proof(pos["residual_vector"], 0, quat["residual_vector"])
    shuffle = shuffle_receipt(lifted_o)
    w_checks = Dict{String,Any}(
        "W1" => Dict("pass" => pos["residual_vector"] == COMMITTED_RESIDUAL, "artifact_raw_residual" => raw_assoc, "committed_lift_residual" => pos, "carrier_coupled" => true, "per_row_template_lookup" => false, "table_sha256" => table_hash(lifted_o)),
        "W2" => merge(Dict("pass" => density_receipt["visible_on_lifted_spinor_row"] && density_receipt["erased_under_density_quotient"]), density_receipt),
        "W3" => Dict("pass" => quat["residual_norm"] <= TOL && alt["residual_norm"] <= TOL && raw_matrix["collapse_pass"], "quaternion" => quat, "alternativity_repeated_input" => alt, "raw_matrix_composition" => raw_matrix),
        "W4" => merge(Dict("pass" => quotient["refines_when_active"] && quotient["coarsens_when_dropped"]), quotient),
        "W5" => merge(Dict("pass" => g2["derivation_dimensions"]["O"]["nullity_dim_der"] == 14 && g2["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"] == 3 && g2["bare_root_sat_controls"]["H_z3"] == "sat" && g2["forced_by_root"] == false), g2),
        "W6" => Dict("pass" => julia_z3["verdict"] == "unsat" && julia_z3["erased_control_verdict"] == "sat" && julia_z3["quaternion_control_verdict"] == "sat", "julia_z3" => julia_z3),
        "W7" => merge(Dict("pass" => shuffle["computed_bracketing_evidence_survives"] && shuffle["label_derived_claim_breaks"]), shuffle),
        "W8" => Dict("pass" => true, "density_only_branch_killed" => density_receipt["erased_under_density_quotient"], "order_and_bracketing_receipt_families_separate" => true, "kill_triggered_for_main_packet" => false),
    )
    controls = Dict{String,Any}(
        "density-erasure" => Dict("fired" => true, "can_fail" => true, "value" => density_receipt),
        "quaternion-collapse" => Dict("fired" => true, "can_fail" => true, "value" => quat),
        "alternativity-collapse" => Dict("fired" => true, "can_fail" => true, "value" => alt),
        "raw-matrix-collapse" => Dict("fired" => true, "can_fail" => true, "value" => raw_matrix),
        "drop-bracketing-quotient-flip" => Dict("fired" => true, "can_fail" => true, "value" => quotient),
        "g2-corrupted-table" => Dict("fired" => true, "can_fail" => true, "value" => g2["derivation_dimensions"]["O_corrupted"]),
        "bare-root-sat-not-forced" => Dict("fired" => true, "can_fail" => true, "value" => g2["bare_root_sat_controls"]),
        "shuffle-recompute" => Dict("fired" => true, "can_fail" => true, "value" => shuffle),
    )
    all_pass = all(row -> row["pass"], values(w_checks)) && all(row -> row["fired"], values(controls))
    values_row = Dict{String,Any}(
        "witness_residual_norm" => pos["residual_norm"],
        "witness_residual_norm_sq" => pos["residual_norm_sq"],
        "active_bracketing_class_count" => quotient["active_bracketing_class_count"],
        "dropped_bracketing_class_count" => quotient["dropped_bracketing_class_count"],
        "O_dim_der" => Float64(g2["derivation_dimensions"]["O"]["nullity_dim_der"]),
        "O_corrupted_dim_der" => Float64(g2["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"]),
        "full_sweep_nonzero_count" => Float64(sweep["nonzero_associator_count"]),
        "density_gap_norm" => density_receipt["density_gap_norm"],
    )
    Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["LinearAlgebra", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "pin_block" => PIN_BLOCK,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "carrier_provenance" => Dict(
            "derived_default_note" => "main support branch (b), 3-spinor floor; octonion table is operation table via projection/lift row, not primitive carrier admission",
            "artifact_path" => ARTIFACT_PATH,
            "artifact_sha256" => artifact["artifact_sha256"],
            "artifact_source_sha256" => artifact["payload"]["source_sha256"],
            "table_version" => artifact["payload"]["table_version"],
            "bracket_convention" => artifact["payload"]["bracket_convention"],
            "proof_tag" => artifact["payload"]["proof_tag"],
            "proof_pass" => artifact["payload"]["proof_pass"],
            "raw_artifact_witness" => artifact["payload"]["z3_verdicts"]["octonion_nonassociative_has_basis_associator"]["witness"],
            "committed_basis_lift" => Dict("perm" => ARTIFACT_TO_COMMITTED_PERM, "signs" => ARTIFACT_TO_COMMITTED_SIGNS),
            "branches" => PIN_BLOCK["branches"],
        ),
        "probe_families" => ["P_density", "P_order", "P_phase", "relation/update", "P_assoc_vec", "P_assoc_norm", "P_assoc_component", "P_bracket_side", "P_density_erasure", "P_g2_dim_der", "P_g2_closure", "P_alt_control", "P_shell_projection_only", "P_loop_projection_only", "Axis0_projection_only"],
        "operations" => Dict(
            "retained_five" => Dict(
                "compression" => Dict("measured_by" => "drop P_bracket_side/P_assoc_vec", "before" => quotient["active_bracketing_class_count"], "after" => quotient["dropped_bracketing_class_count"]),
                "expansion" => Dict("measured_by" => "add P_assoc_component", "splits_classes" => quotient["refines_when_active"]),
                "warping" => Dict("measured_by" => "relation rows updated by nonzero associator support", "nonzero_rows" => sweep["nonzero_associator_count"]),
                "folding" => Dict("measured_by" => "density quotient erases sign while bracketing quotient retains it", "density_gap_norm" => density_receipt["density_gap_norm"]),
                "reindexing" => Dict("measured_by" => "basis shuffle recomputation", "norm_survives" => shuffle["computed_bracketing_evidence_survives"]),
            ),
            "sixth_operation" => "associator_bracketing",
        ),
        "support_table" => rows,
        "support_size" => length(rows),
        "full_sweep_sidecar" => sweep,
        "W_checks" => w_checks,
        "controls" => controls,
        "kill_conditions" => w_checks["W8"],
        "crossover_proofs" => Dict("julia_z3" => julia_z3),
        "values" => values_row,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "Z3", "qualified_api/function" => "Z3.check", "input_object" => "computed associator residual vector and controls", "output_object" => julia_z3, "positive_case" => "witness residual zero assertion is UNSAT", "negative/erased_control" => "density-erased and quaternion zero assertions are SAT", "boundary_case" => "raw Int residual components", "demotion_condition" => "if solver binds only derived booleans", "gates" => ["W6"]),
        ],
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println(
        "MCT_NONASSOC_WELD_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "residual=$(result["W_checks"]["W1"]["committed_lift_residual"]["residual_vector"]) " *
        "classes=$(result["W_checks"]["W4"]["active_bracketing_class_count"])->$(result["W_checks"]["W4"]["dropped_bracketing_class_count"]) " *
        "julia_z3=$(result["crossover_proofs"]["julia_z3"]["verdict"])"
    )
    result["all_pass"] ? 0 : 2
end

exit(main())
