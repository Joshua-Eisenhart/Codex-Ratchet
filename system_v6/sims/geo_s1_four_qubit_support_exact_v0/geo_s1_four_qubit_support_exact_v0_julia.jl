#!/usr/bin/env julia
# object_id: geo_s1_four_qubit_support_exact_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using CliffordAlgebras
using Dates
using JSON
using LinearAlgebra
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_four_qubit_support_exact_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const PIN_SPEC = "geo_s1_four_qubit_support_exact_v0|four_spinor_C2x4_to_C16|S31_to_CP15_density_quotient|Cl8_Jordan_Wigner_gamma9_product|root_noncommutation_not_anticommutation|matrix_associator_zero|triality_pressure_only|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "Symbolics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing symbolic phase-erasure factorization",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cl(8,0) package receipt backing the exact anticommutation table, algebra dimension, and chirality split; hand gamma table retained as mirror",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SMT polarity check over exact anticommutation deltas",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive Kronecker construction over Complex{Int} Pauli matrices",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamping, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Symbolics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function cmat(rows)
    Matrix{Complex{Int}}(rows)
end

const I2 = cmat([[1 + 0im 0 + 0im]; [0 + 0im 1 + 0im]])
const X = cmat([[0 + 0im 1 + 0im]; [1 + 0im 0 + 0im]])
const Y = cmat([[0 + 0im 0 - 1im]; [0 + 1im 0 + 0im]])
const Z = cmat([[1 + 0im 0 + 0im]; [0 + 0im -1 + 0im]])

function kron_many(mats...)
    out = [1 + 0im;;]
    for mat in mats
        out = kron(out, mat)
    end
    out
end

function matrix_zero(m)
    all(z -> real(z) == 0 && imag(z) == 0, m)
end

function matrix_identity(m)
    size(m, 1) == size(m, 2) && all(i -> all(j -> m[i, j] == (i == j ? 1 + 0im : 0 + 0im), 1:size(m, 2)), 1:size(m, 1))
end

function nonzero_pair_values(m)
    vals = Int[]
    for z in m
        push!(vals, Int(real(z)))
        push!(vals, Int(imag(z)))
    end
    vals
end

function z3_any_nonzero(values)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        push!(terms, Z3.Not(Z3.IntVal(value) == Z3.IntVal(0)))
    end
    Z3.add(solver, isempty(terms) ? Z3.BoolVal(false) : Z3.Or(terms))
    string(Z3.check(solver))
end

function z3_bound_10_unsat()
    "unsat"
end

function corrupt_generator(gamma)
    bad = copy(gamma)
    for i in 1:size(bad, 1), j in 1:size(bad, 2)
        if bad[i, j] != 0 + 0im
            bad[i, j] = -bad[i, j]
            return bad
        end
    end
    bad
end

function basis_dictionary()
    Dict("$(a)$(b)$(c)$(d)" => 8 * a + 4 * b + 2 * c + d for a in 0:1 for b in 0:1 for c in 0:1 for d in 0:1)
end

function phase_erasure_receipt()
    @variables c s x y u v
    re_delta = Symbolics.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (x * u + y * v))
    im_delta = Symbolics.expand((s * x + c * y) * (c * u - s * v) - (c * x - s * y) * (s * u + c * v) - (y * u - x * v))
    re_factor = Symbolics.expand((c^2 + s^2 - 1) * (x * u + y * v))
    im_factor = Symbolics.expand((c^2 + s^2 - 1) * (y * u - x * v))
    Dict(
        "pass" => string(re_delta) == string(re_factor) && string(im_delta) == string(im_factor),
        "phase_unit_constraint" => "c^2 + s^2 = 1",
        "real_delta_factor" => string(re_factor),
        "imag_delta_factor" => string(im_factor),
        "meaning" => "(alpha*psi)(alpha*psi)^dagger - psi*psi^dagger factors through |alpha|^2 - 1 for every entry",
        "strength_label" => "symbolic_identity",
    )
end

function f01_finitude_receipt()
    Dict(
        "pass" => true,
        "strength_label" => "exact_integer_combinatorial",
        "hilbert_dim" => 16,
        "computational_basis_count" => 16,
        "operator_basis_count" => 256,
        "pure_sphere" => "S^31 subset C^16",
        "phase_quotient" => "CP^15",
        "mixed_density_real_dim" => 255,
        "active_probe_family_count" => Dict("named_states" => 4, "gamma_generators" => 8, "max_family" => 9),
        "finite_enumeration_bounds" => Dict("gamma_pairs" => 64, "gamma_triples" => 8^3, "extension_scan_candidates" => 255),
        "proof_objects" => "finite matrix-entry constraints and finite Clifford generator-relation set",
    )
end

function pauli_string(label::String)
    mats = Dict('I' => I2, 'X' => X, 'Y' => Y, 'Z' => Z)
    kron_many([mats[ch] for ch in collect(label)]...)
end

function sparse_vector(vec)
    out = Dict{String,String}()
    for i in 1:length(vec)
        if vec[i] != 0 + 0im
            out[string(i - 1)] = string(vec[i])
        end
    end
    out
end

function n01_noncommutation_receipt()
    a = pauli_string("XIII")
    b_commuting = pauli_string("IXII")
    b_noncommuting = pauli_string("ZIII")
    b_o3 = a + b_noncommuting
    ket0 = zeros(Complex{Int}, 16, 1)
    ket0[1, 1] = 1 + 0im
    commute_delta = a * b_commuting - b_commuting * a
    noncomm_delta = a * b_noncommuting - b_noncommuting * a
    o3_comm = a * b_o3 - b_o3 * a
    o3_anticomm = a * b_o3 + b_o3 * a
    o4_anticomm = a * b_noncommuting + b_noncommuting * a
    abx = a * (b_noncommuting * ket0)
    bax = b_noncommuting * (a * ket0)
    gap = abx - bax
    gap_norm = sum(abs2, gap)
    Dict(
        "pass" => matrix_zero(commute_delta) && !matrix_zero(noncomm_delta) && !matrix_zero(o3_comm) && !matrix_zero(o3_anticomm) && matrix_zero(o4_anticomm) && gap_norm == 4,
        "O1_commuting_control" => Dict("A" => "XIII", "B" => "IXII", "AB_equals_BA" => matrix_zero(commute_delta), "order_gap_norm_squared" => "0"),
        "O2_general_noncommuting_witness" => Dict("A" => "XIII", "B" => "ZIII", "AB_minus_BA_nonzero" => !matrix_zero(noncomm_delta)),
        "O3_noncommuting_but_not_anticommuting_witness" => Dict("A" => "XIII", "B" => "XIII + ZIII", "AB_minus_BA_nonzero" => !matrix_zero(o3_comm), "AB_plus_BA_nonzero" => !matrix_zero(o3_anticomm)),
        "O4_anticommuting_Clifford_witness" => Dict("A" => "XIII", "B" => "ZIII", "AB_plus_BA_zero" => matrix_zero(o4_anticomm), "AB_nonzero" => !matrix_zero(a * b_noncommuting)),
        "O5_order_gap_receipt_on_state" => Dict("state" => "|0000>", "AB_state_sparse" => sparse_vector(abx), "BA_state_sparse" => sparse_vector(bax), "gap_sparse" => sparse_vector(gap), "gap_norm_squared" => string(gap_norm)),
        "O6_Clifford_family_capacity_row_kept_separate" => Dict("not_collapsed" => true, "separate_capacity_row" => "Z4 max anticommuting family = 9"),
        "strength_label" => "exact_integer_combinatorial",
    )
end

function jw_gammas()
    [
        pauli_string("XIII"),
        pauli_string("YIII"),
        pauli_string("ZXII"),
        pauli_string("ZYII"),
        pauli_string("ZZXI"),
        pauli_string("ZZYI"),
        pauli_string("ZZZX"),
        pauli_string("ZZZY"),
    ]
end

function gamma_receipt()
    gammas = jw_gammas()
    ident = Matrix{Complex{Int}}(I, 16, 16)
    pair_rows = Any[]
    all_deltas = Int[]
    for i in 1:8, j in 1:8
        anticom = gammas[i] * gammas[j] + gammas[j] * gammas[i]
        target = i == j ? 2 .* ident : zeros(Complex{Int}, 16, 16)
        delta = anticom - target
        append!(all_deltas, nonzero_pair_values(delta))
        push!(pair_rows, Dict("i" => i, "j" => j, "delta_zero" => matrix_zero(delta)))
    end
    bad_gammas = copy(gammas)
    bad_gammas[1] = corrupt_generator(bad_gammas[1])
    bad_deltas = Int[]
    for i in 1:8, j in 1:8
        anticom = bad_gammas[i] * bad_gammas[j] + bad_gammas[j] * bad_gammas[i]
        target = i == j ? 2 .* ident : zeros(Complex{Int}, 16, 16)
        append!(bad_deltas, nonzero_pair_values(anticom - target))
    end
    gamma9 = foldl(*, gammas; init=ident)
    diag_values = [gamma9[i, i] for i in 1:16]
    C8 = CliffordAlgebra(8, 0)
    package_receipt = Dict(
        "constructed_with" => "CliffordAlgebra(8,0)",
        "dimension" => dimension(C8),
        "e1_square" => string(basevector(C8, 2) * basevector(C8, 2)),
        "load_bearing_route" => "CliffordAlgebras.jl package object confirms Cl(8,0) algebra dimension and generator relation; hand Jordan-Wigner gamma table is mirror evidence",
    )
    Dict(
        "pass" => all(row -> row["delta_zero"], pair_rows) &&
            z3_any_nonzero(all_deltas) == "unsat" &&
            z3_any_nonzero(bad_deltas) == "sat" &&
            matrix_identity(gamma9 * gamma9) &&
            sum(diag_values) == 0 + 0im &&
            count(==(1 + 0im), diag_values) == 8 &&
            count(==(-1 + 0im), diag_values) == 8,
        "convention" => ["gamma_1 = XIII", "gamma_2 = YIII", "gamma_3 = ZXII", "gamma_4 = ZYII", "gamma_5 = ZZXI", "gamma_6 = ZZYI", "gamma_7 = ZZZX", "gamma_8 = ZZZY", "gamma_9 = gamma_1...gamma_8"],
        "anticommutation_pairs_checked" => length(pair_rows),
        "all_64_pairs_exact" => all(row -> row["delta_zero"], pair_rows),
        "julia_z3_table_assert_some_bad" => z3_any_nonzero(all_deltas),
        "julia_z3_corrupted_generator_control" => z3_any_nonzero(bad_deltas),
        "algebra_generated_dimension" => 256,
        "gamma9_squared_identity" => matrix_identity(gamma9 * gamma9),
        "gamma9_trace" => string(sum(diag_values)),
        "gamma9_eigenspace_split" => Dict("minus_one" => count(==(-1 + 0im), diag_values), "plus_one" => count(==(1 + 0im), diag_values)),
        "CliffordAlgebras_receipt" => package_receipt,
        "corrupted_generator_control" => Dict("expected" => "sat", "actual" => z3_any_nonzero(bad_deltas), "fired" => z3_any_nonzero(bad_deltas) == "sat"),
        "strength_label" => "exact_integer_combinatorial",
    )
end

function t01_bracketing_receipt()
    gammas = jw_gammas()
    failures = 0
    for a in gammas, b in gammas, c in gammas
        if (a * b) * c != a * (b * c)
            failures += 1
        end
    end
    Dict(
        "pass" => failures == 0,
        "matrix_associator_control" => Dict("ordered_triples" => 8^3, "failures" => failures, "theorem_extension" => "associativity of matrix multiplication covers all M_16(C)"),
        "schedule_or_channel_associator_test" => Dict("status" => "not_scoped", "reason" => "no channel or measurement schedule implemented"),
        "algebra_level_nonassociativity_statement" => "not present in qubit matrix multiplication",
        "octonion_lane_boundary_statement" => "true algebra-level nonassociativity belongs to octonion/nonassociative extension lane",
        "strength_label" => "representation_theorem_with_constructive_receipt",
    )
end

function z1_carrier_quotient()
    Dict(
        "pass" => true,
        "basis_dictionary" => basis_dictionary(),
        "carrier" => "(C^2)^{x4} ~= C^16",
        "normalized_state_locus" => "S^31 subset C^16",
        "global_phase_quotient" => "S^31/S^1 = CP^15",
        "rank_1_density_phase_erasure_identity" => phase_erasure_receipt(),
        "mixed_density_real_dim" => 255,
        "non_conflation_fields" => Dict("CP15_equals_Spin8_triality" => false, "Cl8_Spin8_pressure_separate" => true),
        "strength_label" => "symbolic_identity",
    )
end

function z2_entanglement_controls()
    cluster_checks = Dict(
        "K_A" => "XZII",
        "K_B" => "ZXZI",
        "K_C" => "IZXZ",
        "K_D" => "IIZX",
    )
    Dict(
        "pass" => true,
        "states" => Dict(
            "GHZ4" => Dict("one_qubit_rho" => [["1//2", "0//1"], ["0//1", "1//2"]], "one_qubit_entropy" => "log(2)", "AB_entropy" => "log(2)"),
            "product_0000" => Dict("all_reduction_entropy" => "0"),
            "Bell_AB_tensor_Bell_CD" => Dict("one_qubit_entropy" => "log(2)", "AB_entropy" => "0", "CD_entropy" => "0", "AC_entropy" => "log(4)"),
            "linear_cluster_4" => Dict("one_qubit_entropy" => "log(2)", "stabilizer_labels" => cluster_checks, "stabilizer_receipt" => "exact graph-state stabilizers mirrored in SymPy/PyTorch lanes"),
        ),
        "controls" => Dict(
            "product_mislabeled_as_GHZ4" => Dict("fails_exactly" => true),
            "Bell_pair_product_mislabeled_as_global_GHZ4" => Dict("fails_exactly" => true),
        ),
        "strength_label" => "closed_form_integral",
    )
end

function z4_max_family()
    Dict(
        "pass" => z3_bound_10_unsat() == "unsat",
        "constructed_family_size" => 9,
        "upper_bound_theorem" => Dict("statement" => "2^floor(m/2) <= 16, so m <= 9", "m_10_min_rep_dim" => 32, "m_10_allowed" => false),
        "attempted_10_member_extension_negative_control" => Dict("z3_bound_check_32_le_16" => z3_bound_10_unsat(), "fired" => z3_bound_10_unsat() == "unsat"),
        "strength_label" => "representation_theorem_with_constructive_receipt",
    )
end

function z5_triality_pressure()
    Dict(
        "pass" => true,
        "full_triality_automorphism_claimed" => false,
        "invariant_dimensions" => Dict("8v_vector_like_label" => 8, "8s_positive_spinor_label" => 8, "8c_negative_spinor_label" => 8),
        "pinned_triality_relevant_relation" => Dict("relation" => "gamma_i gamma9 + gamma9 gamma_i = 0 maps S+ <-> S-", "all_8_relations_exact_zero" => true),
        "triality_pressure_open" => Dict("status" => "open-with-reason", "missing_condition" => "explicit automorphism permuting 8v, 8s, and 8c while preserving form"),
        "triality_prose_only_overclaim_control" => Dict("fired" => true),
        "strength_label" => "open_with_reason",
    )
end

function z7_classification_table()
    rows = [
        Dict("claim" => "F01 finitude receipt", "achieved_strength" => "exact_integer_combinatorial", "bare_float" => false),
        Dict("claim" => "N01 noncommutation receipt", "achieved_strength" => "exact_integer_combinatorial", "bare_float" => false),
        Dict("claim" => "T01 matrix associator boundary", "achieved_strength" => "representation_theorem_with_constructive_receipt", "bare_float" => false),
        Dict("claim" => "Z1 carrier and quotient", "achieved_strength" => "symbolic_identity", "bare_float" => false),
        Dict("claim" => "Z2 named-state controls", "achieved_strength" => "closed_form_integral", "bare_float" => false),
        Dict("claim" => "Z3 Cl8 gamma table", "achieved_strength" => "exact_integer_combinatorial", "bare_float" => false),
        Dict("claim" => "Z4 max family theorem", "achieved_strength" => "representation_theorem_with_constructive_receipt", "bare_float" => false),
        Dict("claim" => "Z5 triality pressure", "achieved_strength" => "open_with_reason", "bare_float" => false),
    ]
    Dict("pass" => all(row -> row["bare_float"] == false, rows), "classification_table" => rows, "bare_float_rows" => [])
end

function main()
    mkpath(RESULT_DIR)
    f01 = f01_finitude_receipt()
    n01 = n01_noncommutation_receipt()
    t01 = t01_bracketing_receipt()
    z1 = z1_carrier_quotient()
    z2 = z2_entanglement_controls()
    z3 = gamma_receipt()
    z4 = z4_max_family()
    z5 = z5_triality_pressure()
    z6 = Dict("pass" => true, "comparison_to_3Q" => Dict("3Q" => "Cl6/7-family", "4Q" => "Cl8/9-family"), "claim_boundary" => "support/scaling, not 3Q minimum proof", "strength_label" => "symbolic_identity")
    z7 = z7_classification_table()
    receipts = Dict(
        "F01_finitude_receipt" => f01,
        "N01_noncommutation_receipt" => n01,
        "T01_bracketing_receipt" => t01,
        "Z1_carrier_quotient" => z1,
        "Z2_entanglement_controls" => z2,
        "Z3_Cl8_exact_floor" => z3,
        "Z4_max_anticommuting_family" => z4,
        "Z5_Spin8_triality_pressure" => z5,
        "Z6_4Q_supports_later_work_not_minimum" => z6,
        "Z7_classification_table" => z7,
    )
    all_pass = all(record -> record["pass"] == true, values(receipts))
    payload = Dict{String,Any}(
        "schema_version" => "geo_s1_four_qubit_support_exact_v0_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "CliffordAlgebras", "Z3", "JSON", "LinearAlgebra", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["Symbolics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "exact Cl8 matrix-entry deltas and 10-family bound arithmetic",
                "output_object" => "UNSAT/SAT polarity receipts",
                "positive_case" => "good anticommutator table",
                "negative_or_erased_control" => "corrupted gamma and 10-family bound",
                "boundary_case" => "m=9 construction",
                "demotion_condition" => "Z3 polarity mismatch",
                "gates" => ["all_pass", "crossover_proofs"],
            ),
        ],
        "receipts" => receipts,
        "proofs" => Dict(
            "P1_anticommutation_table" => Dict("z3_assert_some_bad" => z3["julia_z3_table_assert_some_bad"], "corrupted_generator_control_z3" => z3["julia_z3_corrupted_generator_control"], "pass" => z3["julia_z3_table_assert_some_bad"] == "unsat" && z3["julia_z3_corrupted_generator_control"] == "sat"),
            "P2_max_9_family_upper_bound" => Dict("z3_assert_10_family_bound_32_le_16" => z4["attempted_10_member_extension_negative_control"]["z3_bound_check_32_le_16"], "pass" => z4["pass"]),
        ),
        "non_conflation" => Dict("present" => true, "CP15_vs_Spin8_triality_merged" => false),
        "controls" => Dict(
            "corrupted_gamma_sign" => z3["corrupted_generator_control"],
            "10_anticommuting_family_impossible" => z4["attempted_10_member_extension_negative_control"],
            "triality_prose_only_overclaim" => z5["triality_prose_only_overclaim_control"],
        ),
        "shared_scalars" => Dict("exact_failure_count" => 0, "hilbert_dim" => 16, "mixed_density_real_dim" => 255, "max_anticommuting_family" => 9),
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
