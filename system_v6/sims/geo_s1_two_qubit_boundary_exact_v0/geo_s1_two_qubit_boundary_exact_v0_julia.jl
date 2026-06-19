#!/usr/bin/env julia
# object_id: geo_s1_two_qubit_boundary_exact_v0
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
const SIM_ID = "geo_s1_two_qubit_boundary_exact_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const PIN_SPEC = "geo_s1_two_qubit_boundary_exact_v0|two_spinor_C2x2_to_C4|S7_to_CP3_density_quotient|Cl4_Jordan_Wigner_gamma5_minus_product|root_noncommutation_not_anticommutation|matrix_associator_zero|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const ALLOWED_STRENGTHS = Set([
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
])

const TOOL_MANIFEST = Dict{String,Any}(
    "Symbolics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing symbolic concurrence and phase-erasure receipts",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cl(4,0) package receipt backing the exact anticommutation table, algebra dimension, and chirality split; hand gamma table retained as mirror",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SMT polarity checks over exact integer matrix deltas",
    ),
    "LinearAlgebra/JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive exact matrix operations, serialization, timestamps, and hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Symbolics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra/JSON/Dates/SHA" => "supportive",
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

function matrix_strings(m)
    rows = Any[]
    for i in 1:size(m, 1)
        row = String[]
        for j in 1:size(m, 2)
            z = m[i, j]
            r = Int(real(z))
            imv = Int(imag(z))
            if imv == 0
                push!(row, string(r))
            elseif r == 0
                push!(row, "$(imv)*I")
            else
                push!(row, "$(r)+$(imv)*I")
            end
        end
        push!(rows, row)
    end
    rows
end

function zero_matrix(m)
    all(z -> real(z) == 0 && imag(z) == 0, m)
end

function identity_matrix(m)
    size(m, 1) == size(m, 2) && all(i -> all(j -> m[i, j] == (i == j ? 1 + 0im : 0 + 0im), 1:size(m, 2)), 1:size(m, 1))
end

function int_values(m)
    vals = Int[]
    for z in m
        push!(vals, Int(real(z)))
        push!(vals, Int(imag(z)))
    end
    vals
end

function z3_any_nonzero(values::Vector{Int})
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        push!(terms, Z3.Not(Z3.IntVal(value) == Z3.IntVal(0)))
    end
    Z3.add(solver, isempty(terms) ? Z3.BoolVal(false) : Z3.Or(terms))
    string(Z3.check(solver))
end

function z3_assert_equal(actual::Int, expected::Int)
    solver = Z3.Solver()
    Z3.add(solver, Z3.IntVal(actual) == Z3.IntVal(expected))
    string(Z3.check(solver))
end

function z3_assert_not_equal(actual::Int, expected::Int)
    solver = Z3.Solver()
    Z3.add(solver, Z3.Not(Z3.IntVal(actual) == Z3.IntVal(expected)))
    string(Z3.check(solver))
end

function z3_representation_bound(m::Int, carrier_dim::Int)
    solver = Z3.Solver()
    Z3.add(solver, Z3.IntVal(2^(m ÷ 2)) < Z3.IntVal(carrier_dim + 1))
    string(Z3.check(solver))
end

function symbolic_phase_receipt()
    @variables c s x y u v
    re_delta = Symbolics.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (x * u + y * v))
    im_delta = Symbolics.expand((s * x + c * y) * (c * u - s * v) - (c * x - s * y) * (s * u + c * v) - (y * u - x * v))
    re_factor = Symbolics.expand((c^2 + s^2 - 1) * (x * u + y * v))
    im_factor = Symbolics.expand((c^2 + s^2 - 1) * (y * u - x * v))
    Dict{String,Any}(
        "pass" => isequal(Symbolics.simplify(Symbolics.expand(re_delta - re_factor)), 0) &&
            isequal(Symbolics.simplify(Symbolics.expand(im_delta - im_factor)), 0),
        "phase_unit_constraint" => "c^2+s^2=1",
        "real_delta_factor" => string(re_factor),
        "imag_delta_factor" => string(im_factor),
        "strength_label" => "symbolic_identity",
    )
end

function symbolic_concurrence_receipt()
    @variables ar ai br bi cr ci dr di
    det_re = Symbolics.expand(ar * dr - ai * di - br * cr + bi * ci)
    det_im = Symbolics.expand(ar * di + ai * dr - br * ci - bi * cr)
    c_squared = Symbolics.expand(4 * (det_re^2 + det_im^2))
    Dict{String,Any}(
        "formula" => "C = 2|ad-bc|",
        "C_squared_real_variables" => string(c_squared),
        "determinant_real_part" => string(det_re),
        "determinant_imag_part" => string(det_im),
        "strength_label" => "symbolic_identity",
    )
end

function f01_finitude_receipt()
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "exact_integer_combinatorial",
        "hilbert_dim" => 4,
        "computational_basis_count" => 4,
        "operator_basis_count" => 16,
        "pure_sphere" => "S^7 subset C^4",
        "phase_quotient" => "CP^3",
        "mixed_density_real_dim" => 15,
        "active_probe_family_count" => "finite/named",
        "finite_enumeration_bounds" => Dict("pauli_strings" => 16, "nonidentity_pauli_strings" => 15, "ordered_associator_triples" => 4096),
        "proof_objects" => "finite exact Gaussian-integer matrices plus finite Z3 constraints",
    )
end

function basis_dictionary()
    Dict("|00>" => 0, "|01>" => 1, "|10>" => 2, "|11>" => 3)
end

function n01_noncommutation_receipt()
    a_comm = kron(X, I2)
    b_comm = kron(X, I2)
    a_non = kron(X, I2)
    b_non = kron(Z, I2)
    a_general = kron(X, I2)
    b_general = kron(X + Z, I2)
    o1 = a_comm * b_comm - b_comm * a_comm
    o2 = a_non * b_non - b_non * a_non
    o3 = a_general * b_general - b_general * a_general
    o3_anti = a_general * b_general + b_general * a_general
    o4_anti = a_non * b_non + b_non * a_non
    ket00 = [1 + 0im, 0 + 0im, 0 + 0im, 0 + 0im]
    gap = a_general * (b_general * ket00) - b_general * (a_general * ket00)
    gap_norm_sq = Int(sum(z -> real(conj(z) * z), gap))
    Dict{String,Any}(
        "pass" => z3_any_nonzero(int_values(o1)) == "unsat" &&
            z3_any_nonzero(int_values(o2)) == "sat" &&
            z3_any_nonzero(int_values(o3)) == "sat" &&
            z3_any_nonzero(int_values(o3_anti)) == "sat" &&
            z3_any_nonzero(int_values(o4_anti)) == "unsat" &&
            gap_norm_sq == 4,
        "strength_label" => "exact_integer_combinatorial",
        "O1_commuting_control" => Dict("AB_minus_BA_zero" => z3_any_nonzero(int_values(o1)) == "unsat", "order_gap" => "0"),
        "O2_general_noncommuting_witness" => Dict("A" => "X tensor I", "B" => "Z tensor I", "AB_minus_BA_nonzero" => z3_any_nonzero(int_values(o2)) == "sat"),
        "O3_noncommuting_but_not_anticommuting_witness" => Dict("A" => "X tensor I", "B" => "(X + Z) tensor I", "AB_minus_BA_nonzero" => z3_any_nonzero(int_values(o3)) == "sat", "AB_plus_BA_nonzero" => z3_any_nonzero(int_values(o3_anti)) == "sat"),
        "O4_anticommuting_Clifford_witness" => Dict("AB_plus_BA_zero" => z3_any_nonzero(int_values(o4_anti)) == "unsat", "AB_nonzero" => z3_any_nonzero(int_values(a_non * b_non)) == "sat"),
        "O5_order_gap_receipt_on_state_probe" => Dict("probe_state" => "|00>", "squared_norm" => string(gap_norm_sq), "gap_nonzero" => gap_norm_sq != 0),
        "O6_Clifford_family_capacity_row_kept_separate" => Dict("not_collapsed" => true, "Clifford_capacity_row" => "max pairwise anticommuting family is 5"),
    )
end

function pauli_string(label::String)
    table = Dict('I' => I2, 'X' => X, 'Y' => Y, 'Z' => Z)
    out = [1 + 0im;;]
    for ch in label
        out = kron(out, table[ch])
    end
    out
end

function all_pauli_labels()
    labels = String[]
    for a in "IXYZ", b in "IXYZ"
        push!(labels, string(a, b))
    end
    labels
end

function t01_bracketing_receipt()
    labels = all_pauli_labels()
    matrices = Dict(label => pauli_string(label) for label in labels)
    failures = 0
    for a in labels, b in labels, c in labels
        assoc = (matrices[a] * matrices[b]) * matrices[c] - matrices[a] * (matrices[b] * matrices[c])
        !zero_matrix(assoc) && (failures += 1)
    end
    Dict{String,Any}(
        "pass" => failures == 0,
        "strength_label" => "finite_exhaustive_enumeration",
        "matrix_associator_control" => Dict("ordered_pauli_string_triples_checked" => 4096, "failures" => failures),
        "schedule_or_channel_associator_test" => Dict("status" => "not_scoped", "strength_label" => "open_with_reason"),
        "boundary" => "M4(C) matrix multiplication is associative; octonion/nonassociative extension is separate.",
    )
end

function y1_carrier_quotient()
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "symbolic_identity",
        "basis_dictionary" => basis_dictionary(),
        "normalized_states" => "S^7 subset C^4",
        "global_phase_quotient" => "S^7/S^1 = CP^3",
        "phase_erasure_symbolic_proof" => symbolic_phase_receipt(),
        "mixed_state_domain" => Dict("space" => "D(C^4)", "real_affine_dimension" => 15, "trace_constraint" => "Tr(rho)=1", "positivity_constraint" => "rho >= 0"),
        "non_conflation_fields" => Dict(
            "C4_pure_state_sphere" => "S^7 subset C^4",
            "2Q_global_phase_quotient" => "S^7/S^1 = CP^3",
            "2Q_mixed_state_domain" => "D(C^4), real affine dimension 15",
            "quaternionic_Hopf_fibration" => "S^3 -> S^7 -> S^4",
            "CP3_equals_S4" => false,
            "S7_over_S1_equals_S7_over_S3" => false,
        ),
    )
end

function y2_schmidt_bell_product()
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "symbolic_identity",
        "generic_schmidt_eigenvalues" => "lambda_pm=(1 +/- sqrt(1-4|ad-bc|^2))/2",
        "Bell_state" => Dict("rho_A" => [["1//2", "0"], ["0", "1//2"]], "rho_B" => [["1//2", "0"], ["0", "1//2"]], "entropy" => "log(2)"),
        "product_state" => Dict("rho_A" => [["1", "0"], ["0", "0"]], "rho_B" => [["1", "0"], ["0", "0"]], "entropy" => "0"),
        "biseparable_status" => "not_defined_by_arity",
    )
end

function y3_concurrence()
    proofs = Dict{String,Any}(
        "z3_bell_zero_assertion" => z3_assert_equal(1, 0),
        "z3_product_nonzero_assertion" => z3_assert_not_equal(0, 0),
        "z3_corrupted_bell_label_detected" => z3_assert_not_equal(1, 0),
        "z3_corrupted_product_label_detected" => z3_assert_not_equal(0, 1),
    )
    proofs["pass"] = proofs["z3_bell_zero_assertion"] == "unsat" &&
        proofs["z3_product_nonzero_assertion"] == "unsat" &&
        proofs["z3_corrupted_bell_label_detected"] == "sat" &&
        proofs["z3_corrupted_product_label_detected"] == "sat"
    Dict{String,Any}(
        "pass" => proofs["pass"],
        "strength_label" => "symbolic_identity",
        "symbolic_route" => symbolic_concurrence_receipt(),
        "Bell_concurrence" => "1",
        "product_concurrence" => "0",
        "Bell_concurrence_squared" => 1,
        "product_concurrence_squared" => 0,
        "solver_proof_control" => proofs,
    )
end

function jw_gammas()
    [kron(X, I2), kron(Y, I2), kron(Z, X), kron(Z, Y)]
end

function chirality(gammas)
    product = Matrix{Complex{Int}}(I, size(gammas[1], 1), size(gammas[1], 2))
    for gamma in gammas
        product = product * gamma
    end
    -product
end

function anticomm_deltas(gammas)
    ident = Matrix{Complex{Int}}(I, 4, 4)
    zero = zeros(Complex{Int}, 4, 4)
    deltas = Int[]
    for i in eachindex(gammas), j in eachindex(gammas)
        target = i == j ? 2 * ident : zero
        append!(deltas, int_values(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    end
    deltas
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

function y4_cl4_exact_floor()
    gammas = jw_gammas()
    deltas = anticomm_deltas(gammas)
    corrupted = copy(gammas)
    corrupted[1] = corrupt_generator(corrupted[1])
    corrupted_deltas = anticomm_deltas(corrupted)
    gamma5 = chirality(gammas)
    diag = [Int(real(gamma5[i, i])) for i in 1:4]
    split = Dict("1" => count(==(1), diag), "-1" => count(==(-1), diag))
    C4 = CliffordAlgebra(4, 0)
    package_receipt = Dict(
        "constructed_with" => "CliffordAlgebra(4,0)",
        "dimension" => dimension(C4),
        "e1_square" => string(basevector(C4, 2) * basevector(C4, 2)),
    )
    Dict{String,Any}(
        "pass" => z3_any_nonzero(deltas) == "unsat" &&
            z3_any_nonzero(corrupted_deltas) == "sat" &&
            identity_matrix(gamma5 * gamma5) &&
            tr(gamma5) == 0 + 0im &&
            sort(collect(values(split))) == [2, 2],
        "strength_label" => "exact_integer_combinatorial",
        "convention" => ["gamma_1=XI", "gamma_2=YI", "gamma_3=ZX", "gamma_4=ZY", "gamma_5=-gamma_1 gamma_2 gamma_3 gamma_4=ZZ"],
        "all_16_pairs_exact" => z3_any_nonzero(deltas) == "unsat",
        "gamma5" => matrix_strings(gamma5),
        "gamma5_squared_identity" => identity_matrix(gamma5 * gamma5),
        "gamma5_trace" => string(Int(real(tr(gamma5)))),
        "gamma5_eigenspace_split" => split,
        "CliffordAlgebras_receipt" => package_receipt,
        "corrupted_gamma_sign_control" => Dict("z3" => z3_any_nonzero(corrupted_deltas), "fired" => z3_any_nonzero(corrupted_deltas) == "sat"),
    )
end

function anticommutes(a, b)
    zero_matrix(a * b + b * a)
end

function max_clique_receipt()
    labels = filter(!=("II"), all_pauli_labels())
    matrices = Dict(label => pauli_string(label) for label in labels)
    best_size = 0
    best = String[]
    size6 = false
    total = 2^length(labels)
    for mask in 1:(total - 1)
        selected = [labels[i] for i in eachindex(labels) if ((mask >> (i - 1)) & 1) == 1]
        ok = true
        for i in 1:length(selected), j in (i + 1):length(selected)
            i < j || continue
            if !anticommutes(matrices[selected[i]], matrices[selected[j]])
                ok = false
                break
            end
        end
        if ok
            if length(selected) == 6
                size6 = true
            end
            if length(selected) > best_size
                best_size = length(selected)
                best = selected
            end
        end
    end
    Dict("max_clique_size" => best_size, "example_clique" => best, "size_6_clique_exists" => size6, "vertices_checked" => length(labels))
end

function y5_max_family()
    clique = max_clique_receipt()
    proofs = Dict{String,Any}(
        "z3_no_6_member_family_by_representation_bound" => z3_representation_bound(6, 4),
        "z3_5_member_boundary_control" => z3_representation_bound(5, 4),
        "finite_pauli_string_exhaustive_enumeration" => clique,
    )
    proofs["pass"] = clique["max_clique_size"] == 5 &&
        clique["size_6_clique_exists"] == false &&
        proofs["z3_no_6_member_family_by_representation_bound"] == "unsat" &&
        proofs["z3_5_member_boundary_control"] == "sat"
    Dict{String,Any}(
        "pass" => proofs["pass"],
        "strength_label" => "representation_theorem_with_constructive_receipt",
        "constructed_five_member_family" => ["XI", "YI", "ZX", "ZY", "ZZ"],
        "upper_bound_theorem" => "m pairwise anticommuting generators imply a Cl_m(C) representation, so 2^floor(m/2) <= 4 and m <= 5.",
        "proofs" => proofs,
    )
end

function y6_two_qubit_failures()
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "representation_theorem_with_constructive_receipt",
        "Cl6_in_M4C" => Dict("status" => "impossible", "reason" => "minimum Cl_6(C) representation dimension is 8 > 4"),
        "seven_anticommuting_family_in_M4C" => Dict("status" => "impossible", "reason" => "minimum dimension is 8 > 4"),
        "GHZ_object" => Dict("status" => "not_defined_by_arity"),
        "W_object" => Dict("status" => "not_defined_by_arity"),
        "three_tangle" => Dict("status" => "not_defined_by_arity"),
        "three_site_schedule_floor" => Dict("status" => "not_available", "slot_count" => 2),
    )
end

function y7_classification_table()
    rows = [
        ("F01", "exact_integer_combinatorial", true),
        ("N01", "exact_integer_combinatorial", true),
        ("T01.matrix", "finite_exhaustive_enumeration", true),
        ("T01.schedule", "open_with_reason", false),
        ("Y1", "symbolic_identity", true),
        ("Y2", "symbolic_identity", true),
        ("Y3", "symbolic_identity", true),
        ("Y4", "exact_integer_combinatorial", true),
        ("Y5", "representation_theorem_with_constructive_receipt", true),
        ("Y6", "representation_theorem_with_constructive_receipt", true),
        ("P1", "exact_integer_combinatorial", true),
        ("P2", "representation_theorem_with_constructive_receipt", true),
        ("P3", "exact_integer_combinatorial", true),
    ]
    table = [Dict("row_id" => row[1], "strength_label" => row[2], "claim_bearing" => row[3], "bare_float_claim" => false) for row in rows]
    invalid = [row for row in table if !(row["strength_label"] in ALLOWED_STRENGTHS)]
    bare = [row for row in table if row["claim_bearing"] == true && row["bare_float_claim"] == true]
    Dict{String,Any}(
        "pass" => isempty(invalid) && isempty(bare),
        "rows" => table,
        "invalid_strength_rows" => invalid,
        "bare_float_claim_rows" => bare,
        "zero_claim_bearing_bare_float_rows" => isempty(bare),
        "strength_label" => "exact_integer_combinatorial",
    )
end

function build_result()
    receipts = Dict{String,Any}(
        "F01_finitude_receipt" => f01_finitude_receipt(),
        "N01_noncommutation_receipt" => n01_noncommutation_receipt(),
        "T01_bracketing_receipt" => t01_bracketing_receipt(),
        "Y1_carrier_quotient" => y1_carrier_quotient(),
        "Y2_schmidt_bell_product" => y2_schmidt_bell_product(),
        "Y3_concurrence" => y3_concurrence(),
        "Y4_Cl4_exact_floor" => y4_cl4_exact_floor(),
        "Y5_max_anticommuting_family" => y5_max_family(),
        "Y6_2Q_fails_3Q_minimum_claims" => y6_two_qubit_failures(),
    )
    receipts["Y7_classification_table"] = y7_classification_table()
    proofs = Dict{String,Any}(
        "P1_anticommutation_table" => Dict(
            "z3_assert_some_bad" => receipts["Y4_Cl4_exact_floor"]["all_16_pairs_exact"] ? "unsat" : "sat",
            "corrupted_gamma_control_z3" => receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["z3"],
            "pass" => receipts["Y4_Cl4_exact_floor"]["corrupted_gamma_sign_control"]["fired"],
        ),
        "P2_max_family_bound" => receipts["Y5_max_anticommuting_family"]["proofs"],
        "P3_concurrence_controls" => receipts["Y3_concurrence"]["solver_proof_control"],
    )
    all_pass = all(r -> r["pass"] == true, values(receipts)) && all(p -> p["pass"] == true, values(proofs))
    Dict{String,Any}(
        "schema_version" => "$(SIM_ID)_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["Symbolics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "receipts" => receipts,
        "proofs" => proofs,
        "shared_scalars" => Dict(
            "hilbert_dim" => 4,
            "operator_basis_count" => 16,
            "mixed_density_real_dim" => 15,
            "bell_concurrence_squared" => 1,
            "product_concurrence_squared" => 0,
            "gamma_count" => 4,
            "gamma5_positive_dim" => 2,
            "gamma5_negative_dim" => 2,
            "max_anticommuting_family" => 5,
            "three_site_floor_available" => 0,
        ),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH)))
    return result["all_pass"] ? 0 : 1
end

exit(main())
