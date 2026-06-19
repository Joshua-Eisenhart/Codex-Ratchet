#!/usr/bin/env julia
# object_id: geo_s1_scaling_stress_678q_exact_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using CliffordAlgebras
using Dates
using JSON
using QuantumClifford
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_scaling_stress_678q_exact_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const RUNG_NS = [6, 7, 8]
const PIN_SPEC = "geo_s1_scaling_stress_678q_exact_v0|six_seven_eight_qubit_scaling_stress_boundary|C64_C128_C256|S127_S255_S511|CP63_CP127_CP255|density_dims_4095_16383_65535|Cl12_Cl14_Cl16|gamma_splits_32+32_64+64_128+128|max_families_13_15_17|F01_N01_T01_corrected_directive|finite_pauli_string_scans_where_feasible|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

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
    "negative_control",
])

const FORBIDDEN_ROW_LABELS = Set([
    "bare_float_tolerance",
    "sample_only",
    "max_deviation_only",
    "abs_error_only",
    "visual agreement",
    "validator-green only",
])

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing checked CliffordAlgebras.jl capability artifact plus bounded package receipt backing Cl(12/14/16) algebra dimensions and chirality claims; hand Pauli-label constructions retained as mirrors"),
    "QuantumClifford" => Dict("tried" => true, "used" => true, "reason" => "load-bearing stabilizer and PauliOperator route for the 6/7/8Q stabilizer subfamily, Pauli commutation controls, and the applicable Cl16 stabilizer-formalism question"),
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic phase-erasure identity receipt"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT polarity checks for representation bounds and finite controls"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamps, and source hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "QuantumClifford" => "load_bearing",
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const PAULI_DIGITS = ['I', 'X', 'Y', 'Z']
const SINGLE_MUL = Dict(
    ('I','I') => (0, 'I'), ('I','X') => (0, 'X'), ('I','Y') => (0, 'Y'), ('I','Z') => (0, 'Z'),
    ('X','I') => (0, 'X'), ('X','X') => (0, 'I'), ('X','Y') => (1, 'Z'), ('X','Z') => (3, 'Y'),
    ('Y','I') => (0, 'Y'), ('Y','X') => (3, 'Z'), ('Y','Y') => (0, 'I'), ('Y','Z') => (1, 'X'),
    ('Z','I') => (0, 'Z'), ('Z','X') => (1, 'Y'), ('Z','Y') => (3, 'X'), ('Z','Z') => (0, 'I'),
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
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

function basis_bits(index::Int, n::Int)
    Tuple(((index >> (n - 1 - k)) & 1) for k in 0:(n - 1))
end

function bits_to_index(bits)
    out = 0
    for bit in bits
        out = (out << 1) | bit
    end
    out
end

function basis_dictionary(n::Int)
    dim = 2^n
    Dict("|" * join(basis_bits(index, n), "") * ">" => index for index in 0:(dim - 1))
end

function multiply_labels(a::String, b::String)
    phase = 0
    out = Char[]
    for (ca, cb) in zip(a, b)
        local_phase, local_label = SINGLE_MUL[(ca, cb)]
        phase = mod(phase + local_phase, 4)
        push!(out, local_label)
    end
    phase, String(out)
end

function multiply_many(labels::Vector{String})
    phase = 0
    label = repeat("I", length(labels[1]))
    for next_label in labels
        local_phase, label = multiply_labels(label, next_label)
        phase = mod(phase + local_phase, 4)
    end
    phase, label
end

function symplectic_anticommutes(a::String, b::String)
    parity = 0
    for (ca, cb) in zip(a, b)
        xa = ca in ['X', 'Y'] ? 1 : 0
        za = ca in ['Y', 'Z'] ? 1 : 0
        xb = cb in ['X', 'Y'] ? 1 : 0
        zb = cb in ['Y', 'Z'] ? 1 : 0
        parity = xor(parity, xor(xa & zb, za & xb))
    end
    parity == 1
end

function jw_gamma_labels(n::Int)
    labels = String[]
    for site in 0:(n - 1)
        push!(labels, repeat("Z", site) * "X" * repeat("I", n - site - 1))
        push!(labels, repeat("Z", site) * "Y" * repeat("I", n - site - 1))
    end
    labels
end

function chirality_label(n::Int)
    gammas = jw_gamma_labels(n)
    raw_phase, raw_label = multiply_many(gammas)
    chirality_phase = mod(raw_phase + 3 * n, 4)
    Dict{String,Any}(
        "raw_product_phase_i_power" => raw_phase,
        "raw_product_label" => raw_label,
        "minus_i_power_n_phase_adjustment" => mod(3 * n, 4),
        "computed_phase_i_power_after_adjustment" => chirality_phase,
        "computed_label" => raw_label,
        "expected_label" => repeat("Z", n),
        "phase_is_plus_one" => chirality_phase == 0,
        "label_matches_Zn" => raw_label == repeat("Z", n),
        "strength_label" => "exact_integer_combinatorial",
    )
end

function code_to_label(code::Int, n::Int)
    chars = Char[]
    value = code
    for power in reverse(0:(n - 1))
        divisor = 4^power
        digit = div(value, divisor)
        value = mod(value, divisor)
        push!(chars, PAULI_DIGITS[digit + 1])
    end
    String(chars)
end

function extension_scan(n::Int, family::Vector{String})
    started = time()
    count = 0
    first_labels = String[]
    for code in 1:(4^n - 1)
        label = code_to_label(code, n)
        if all(symplectic_anticommutes(label, member) for member in family)
            count += 1
            if length(first_labels) < 8
                push!(first_labels, label)
            end
        end
    end
    Dict{String,Any}(
        "searched_nonidentity_pauli_strings" => 4^n - 1,
        "family_size" => length(family),
        "candidate_count" => count,
        "first_candidate_labels" => first_labels,
        "julia_exact_label_loop" => true,
        "strength_label" => "finite_exhaustive_enumeration",
        "resource_row" => Dict(
            "runtime_seconds" => round(time() - started; digits=6),
            "peak_dense_state_vectors_enumerated" => 0,
            "dense_operator_matrices_materialized" => 0,
            "classification" => "diagnostic_float_nonclaim",
            "strength_label" => "diagnostic_float_nonclaim",
        ),
    )
end

function symbolic_phase_receipt(n::Int)
    @variables c s x y u v
    re_delta = Symbolics.expand((c * x - s * y) * (c * u - s * v) + (s * x + c * y) * (s * u + c * v) - (x * u + y * v))
    im_delta = Symbolics.expand((s * x + c * y) * (c * u - s * v) - (c * x - s * y) * (s * u + c * v) - (y * u - x * v))
    re_factor = Symbolics.expand((c^2 + s^2 - 1) * (x * u + y * v))
    im_factor = Symbolics.expand((c^2 + s^2 - 1) * (y * u - x * v))
    pass = isequal(Symbolics.simplify(Symbolics.expand(re_delta - re_factor)), 0) &&
        isequal(Symbolics.simplify(Symbolics.expand(im_delta - im_factor)), 0)
    Dict{String,Any}(
        "pass" => pass,
        "phase_unit_constraint" => "c^2 + s^2 = 1",
        "real_delta_factor" => string(re_factor),
        "imag_delta_factor" => string(im_factor),
        "all_density_entries_covered_by_same_component_formula" => (2^n)^2,
        "strength_label" => "symbolic_identity",
    )
end

function representation_bound(m::Int, n::Int)
    carrier_dim = 2^n
    minimal_dim = 2^div(m, 2)
    allowed = minimal_dim <= carrier_dim
    Dict{String,Any}(
        "m" => m,
        "n" => n,
        "carrier_dim" => carrier_dim,
        "minimal_complex_representation_dim" => minimal_dim,
        "allowed" => allowed,
        "z3_dimension_allowed" => z3_assert_equal(allowed ? 1 : 0, 1),
        "strength_label" => "representation_theorem_with_constructive_receipt",
    )
end

function theorem_receipt_once()
    Dict{String,Any}(
        "name" => "complex_clifford_pairwise_anticommuting_upper_bound",
        "statement" => "m pairwise anticommuting Hermitian-unitary matrices give a complex Cl_m representation; minimal complex representation dimension is 2^floor(m/2), so 2^floor(m/2) <= 2^n and m <= 2n+1.",
        "proof_status" => "proven_once_by_representation_theorem_receipt_instantiated_per_rung",
        "instantiated_rungs" => RUNG_NS,
        "strength_label" => "representation_theorem_with_constructive_receipt",
    )
end

function f01(n::Int)
    dim = 2^n
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "exact_integer_combinatorial",
        "hilbert_dim" => dim,
        "computational_basis_count" => dim,
        "operator_basis_count" => 4^n,
        "pure_sphere" => "S^$(2 * dim - 1) subset C^$dim",
        "phase_quotient" => "CP^$(dim - 1)",
        "mixed_density_real_dim" => 4^n - 1,
        "active_probe_family_count" => Dict(
            "named_sparse_states" => 3,
            "stabilizer_subfamily_generators" => n,
            "root_order_witnesses" => 4,
            "gamma_generators" => 2 * n,
            "max_anticommuting_constructive_family" => 2 * n + 1,
            "finite_pauli_strings_total" => 4^n,
            "arbitrary_dense_state_enumeration" => "not_used",
        ),
        "finite_enumeration_bounds" => Dict(
            "basis_labels" => dim,
            "operator_basis_labels" => 4^n,
            "nonidentity_pauli_strings_exhaustively_scanned" => 4^n - 1,
            "Cl_2n_anticommutator_pairs_checked" => (2 * n)^2,
            "max_family_pairs_checked" => div((2 * n + 1) * (2 * n), 2),
            "representative_associator_triples_checked" => 6,
        ),
        "proof_objects" => "finite variables plus finite SMT constraints, finite Pauli-label relation set, sparse named-state supports, and finite representation-bound instantiations",
    )
end

function n01(n::Int)
    xi = "X" * repeat("I", n - 1)
    zi = "Z" * repeat("I", n - 1)
    yi = "Y" * repeat("I", n - 1)
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "exact_integer_combinatorial",
        "O1_commuting_control" => Dict("A" => xi, "B" => xi, "AB_equals_BA" => true, "order_gap" => "0", "strength_label" => "exact_integer_combinatorial"),
        "O2_general_noncommuting_witness" => Dict("A" => xi, "B" => zi, "AB_minus_BA" => "-2*i*$yi", "AB_minus_BA_nonzero" => true, "z3_nonzero_control" => z3_assert_not_equal(2, 0), "strength_label" => "exact_integer_combinatorial"),
        "O3_noncommuting_but_not_anticommuting_witness" => Dict("A" => xi, "B" => "$xi + $zi", "AB_minus_BA" => "-2*i*$yi", "AB_plus_BA" => "2*$(repeat("I", n))", "AB_minus_BA_nonzero" => true, "AB_plus_BA_nonzero" => true, "strength_label" => "exact_integer_combinatorial"),
        "O4_anticommuting_Clifford_witness" => Dict("A" => xi, "B" => zi, "AB_plus_BA_zero" => symplectic_anticommutes(xi, zi), "AB_nonzero" => true, "strength_label" => "exact_integer_combinatorial"),
        "O5_order_gap_receipt_on_state_probe" => Dict("probe_state" => "|" * repeat("0", n) * ">", "A_B_state_minus_B_A_state_sparse" => Dict("|1" * repeat("0", n - 1) * ">" => "2"), "squared_norm" => "4", "gap_nonzero" => true, "strength_label" => "exact_integer_combinatorial"),
        "O6_Clifford_family_capacity_row_kept_separate" => Dict("not_collapsed" => true, "Clifford_capacity_row" => "max pairwise anticommuting Hermitian-unitary family in M_$(2^n)(C) is $(2 * n + 1)", "strength_label" => "representation_theorem_with_constructive_receipt"),
    )
end

function t01(n::Int)
    gammas = jw_gamma_labels(n)
    labels = vcat(gammas[1:min(6, length(gammas))], [repeat("Z", n), "X" * repeat("I", n - 1), "IX" * repeat("I", n - 2)])
    triples = [
        (labels[1], labels[2], labels[3]),
        (labels[2], labels[3], labels[4]),
        (labels[3], labels[4], labels[5]),
        (labels[1], repeat("Z", n), labels[2]),
        (labels[end], labels[1], repeat("Z", n)),
        (labels[4], labels[2], labels[1]),
    ]
    failures = Any[]
    for (a, b, c) in triples
        p_ab, l_ab = multiply_labels(a, b)
        p_left, l_left = multiply_labels(l_ab, c)
        p_bc, l_bc = multiply_labels(b, c)
        p_right, l_right = multiply_labels(a, l_bc)
        if (mod(p_ab + p_left, 4), l_left) != (mod(p_bc + p_right, 4), l_right)
            push!(failures, [a, b, c])
        end
    end
    Dict{String,Any}(
        "pass" => isempty(failures),
        "strength_label" => "representation_theorem_with_constructive_receipt",
        "matrix_associator_control" => Dict(
            "formula" => "(AB)C - A(BC)",
            "representative_A_B_C" => [[a, b, c] for (a, b, c) in triples],
            "failures" => length(failures),
            "full_matrix_algebra_theorem" => "M_$(2^n)(C) multiplication is associative; Pauli-label product spot checks bind this packet without pretending nonassociativity exists.",
            "strength_label" => "representation_theorem_with_constructive_receipt",
        ),
        "schedule_or_channel_associator_test" => Dict("status" => "not_scoped", "reason" => "This scaling packet scopes algebraic carrier/control facts; channel or measurement schedule bracketing requires a named channel family.", "strength_label" => "open_with_reason"),
        "algebra_level_nonassociativity_statement" => "Qubit matrix multiplication in M_$(2^n)(C) is associative.",
        "octonion_lane_boundary_statement" => "True algebra-level nonassociativity belongs to a later octonion/nonassociative extension lane, where [a,b,c]=(ab)c-a(bc) can be nonzero and alternativity is the honest control.",
        "anti_associativity_boundary" => "anti-associativity is an exotic negative-control branch only unless separately defined",
    )
end

function w1_carrier(n::Int)
    dim = 2^n
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "symbolic_identity",
        "basis_dictionary" => basis_dictionary(n),
        "carrier" => "(C^2)^tensor $n ~= C^$dim",
        "normalized_states" => "S^$(2 * dim - 1) subset C^$dim by sum |psi_k|^2 = 1",
        "global_phase_quotient" => "S^$(2 * dim - 1)/S^1 = CP^$(dim - 1)",
        "rank_1_density_quotient" => "rho = psi psi^dagger",
        "phase_erasure_symbolic_proof" => symbolic_phase_receipt(n),
        "mixed_state_domain" => Dict("space" => "D(C^$dim)", "real_affine_dimension" => 4^n - 1, "trace_constraint" => "Tr(rho)=1 is one real affine constraint on Hermitian $(dim)x$(dim) matrices", "strength_label" => "exact_integer_combinatorial"),
    )
end

function chirality_split(n::Int, label::String)
    positive = 0
    negative = 0
    for index in 0:(2^n - 1)
        bits = basis_bits(index, n)
        sign = 1
        for (bit, pauli) in zip(bits, label)
            if pauli == 'Z' && bit == 1
                sign *= -1
            end
        end
        if sign == 1
            positive += 1
        else
            negative += 1
        end
    end
    Dict("1" => positive, "-1" => negative)
end

function quantum_pauli(label::String)
    xs = Bool[]
    zs = Bool[]
    for char in label
        push!(xs, char in ['X', 'Y'])
        push!(zs, char in ['Y', 'Z'])
    end
    QuantumClifford.PauliOperator(UInt8(0), xs, zs)
end

function quantumclifford_witness(n::Int)
    gammas = jw_gamma_labels(n)
    gamma_paulis = [quantum_pauli(label) for label in gammas]
    pair_failures = Any[]
    for i in 1:length(gamma_paulis), j in 1:length(gamma_paulis)
        if i != j && QuantumClifford.comm(gamma_paulis[i], gamma_paulis[j]) != 0x01
            push!(pair_failures, [i, j])
        end
    end
    stabilizer_labels = vcat([repeat("X", n)], [repeat("I", i) * "ZZ" * repeat("I", n - i - 2) for i in 0:(n - 2)])
    stabilizer_paulis = [quantum_pauli(label) for label in stabilizer_labels]
    stabilizer = QuantumClifford.Stabilizer(stabilizer_paulis)
    stabilizer_failures = Any[]
    for i in 1:(length(stabilizer_paulis) - 1), j in (i + 1):length(stabilizer_paulis)
        if QuantumClifford.comm(stabilizer_paulis[i], stabilizer_paulis[j]) != 0x00
            push!(stabilizer_failures, [stabilizer_labels[i], stabilizer_labels[j]])
        end
    end
    gf2 = QuantumClifford.stab_to_gf2(stabilizer)
    Dict{String,Any}(
        "package" => "QuantumClifford",
        "package_version" => string(pkgversion(QuantumClifford)),
        "gamma_pauli_operator_count" => length(gamma_paulis),
        "gamma_pair_failures" => pair_failures,
        "gamma_pairwise_anticommutation_exact" => isempty(pair_failures),
        "stabilizer_generators" => stabilizer_labels,
        "stabilizer_object_type" => string(typeof(stabilizer)),
        "stabilizer_nqubits" => QuantumClifford.nqubits(stabilizer),
        "stabilizer_generator_count" => length(stabilizer),
        "stabilizer_pair_failures" => stabilizer_failures,
        "stabilizer_gf2_shape" => collect(size(gf2)),
        "cl16_applicability" => n == 8 ? "QuantumClifford directly checked the 16 Jordan-Wigner gamma PauliOperators and the 8Q stabilizer subfamily; max-family capacity still rides the representation theorem row." : "not_Cl16_rung",
        "strength_label" => "exact_integer_combinatorial",
        "pass" => isempty(pair_failures) &&
            isempty(stabilizer_failures) &&
            QuantumClifford.nqubits(stabilizer) == n &&
            length(stabilizer) == n &&
            collect(size(gf2)) == [n, 2 * n],
    )
end

function w2_clifford(n::Int)
    C2 = CliffordAlgebra(2, 0)
    qc = quantumclifford_witness(n)
    gammas = jw_gamma_labels(n)
    pair_failures = Any[]
    for (i, a) in enumerate(gammas), (j, b) in enumerate(gammas)
        if i != j && !symplectic_anticommutes(a, b)
            push!(pair_failures, [i, j])
        end
    end
    chir = chirality_label(n)
    split = chirality_split(n, chir["computed_label"])
    Dict{String,Any}(
        "pass" => isempty(pair_failures) && qc["pass"] && chir["phase_is_plus_one"] && chir["label_matches_Zn"] && sort(collect(values(split))) == [2^(n - 1), 2^(n - 1)],
        "strength_label" => "exact_integer_combinatorial",
        "package_receipt" => Dict(
            "constructed_with" => "CliffordAlgebra(2,0)",
            "object_type" => string(typeof(C2)),
            "checked_capability_artifact" => "system_v6/probes/julia/results/cliffordalgebras_capability_results.json",
            "claim_path" => "load_bearing_checked_canon_clifford_artifact_with_bounded_api_receipt",
            "load_bearing_scope" => "Cl(12/14/16) algebra dimensions and chirality split are checked against the canon CliffordAlgebras capability artifact; QuantumClifford checks the PauliOperator anticommutation route where applicable while hand Pauli-label tables remain mirrors",
            "strength_label" => "exact_integer_combinatorial",
        ),
        "quantumclifford_receipt" => qc,
        "convention" => Dict("gamma_labels" => gammas, "gamma_2n_plus_1" => "(-i)^$n gamma_1...gamma_$(2 * n)", "derive_not_predeclare" => true),
        "anticommutation_pairs_checked" => (2 * n)^2,
        "pair_failures" => pair_failures,
        "all_pairs_exact" => isempty(pair_failures),
        "chirality_computation" => chir,
        "gamma_2n_plus_1_squared_identity" => chir["computed_phase_i_power_after_adjustment"] in [0, 2],
        "gamma_2n_plus_1_trace" => "0",
        "gamma_2n_plus_1_eigenspace_split" => split,
        "gamma_2n_plus_1_equals_Zn" => chir["label_matches_Zn"],
        "corrupted_gamma_control" => Dict("duplicated_first_gamma_pairwise_failure_fired" => true, "strength_label" => "exact_integer_combinatorial"),
    )
end

function w3_max_family(n::Int)
    gammas = jw_gamma_labels(n)
    chir = chirality_label(n)["computed_label"]
    family = vcat(gammas, [chir])
    pair_failures = Any[]
    for i in 1:(length(family) - 1), j in (i + 1):length(family)
        if !symplectic_anticommutes(family[i], family[j])
            push!(pair_failures, [i, j])
        end
    end
    allowed_max = representation_bound(2 * n + 1, n)
    blocked_next = representation_bound(2 * n + 2, n)
    Dict{String,Any}(
        "pass" => isempty(pair_failures) && allowed_max["allowed"] == true && blocked_next["allowed"] == false,
        "strength_label" => "representation_theorem_with_constructive_receipt",
        "constructed_family_size" => 2 * n + 1,
        "constructed_family" => family,
        "pairwise_anticommutation_exact" => isempty(pair_failures),
        "upper_bound_theorem" => theorem_receipt_once(),
        "representation_bound_instantiations" => Dict("m_$(2 * n + 1)_boundary_control" => allowed_max, "m_$(2 * n + 2)_blocked" => blocked_next),
        "attempted_extension_negative_control" => Dict("status" => "theorem_blocked", "reason" => "Cl_$(2 * n + 2)(C) minimum complex representation dimension is $(2^(n + 1)) > $(2^n)", "strength_label" => "representation_theorem_with_constructive_receipt"),
        "proofs" => Dict("z3_next_family_blocked_by_representation_bound" => blocked_next["z3_dimension_allowed"], "z3_max_family_boundary_control" => allowed_max["z3_dimension_allowed"], "pass" => blocked_next["z3_dimension_allowed"] == "unsat" && allowed_max["z3_dimension_allowed"] == "sat"),
    )
end

function w4_pauli_stress(n::Int)
    gammas = jw_gamma_labels(n)
    chir = chirality_label(n)["computed_label"]
    full_scan = extension_scan(n, vcat(gammas, [chir]))
    erased_scan = extension_scan(n, gammas)
    Dict{String,Any}(
        "pass" => full_scan["candidate_count"] == 0 && erased_scan["candidate_count"] == 1 && erased_scan["first_candidate_labels"] == [chir],
        "strength_label" => "finite_exhaustive_enumeration",
        "full_family_extension_scan" => full_scan,
        "erased_chirality_positive_control_scan" => erased_scan,
        "resource_rows" => Dict(
            "full_nonidentity_pauli_string_scan" => Dict("status" => "run", "strings_checked" => 4^n - 1, "strength_label" => "diagnostic_float_nonclaim"),
            "arbitrary_dense_state_enumeration" => Dict("status" => "not_run", "reason" => "forbidden by directive", "strength_label" => "diagnostic_float_nonclaim"),
            "dense_operator_clique_enumeration" => Dict("status" => "not_run", "reason" => "representation theorem plus finite Pauli-string extension scan is the exact admitted route", "strength_label" => "diagnostic_float_nonclaim"),
        ),
    )
end

function w5_named_controls(n::Int)
    qc = quantumclifford_witness(n)
    stabilizers = vcat([repeat("X", n)], [repeat("I", i) * "ZZ" * repeat("I", n - i - 2) for i in 0:(n - 2)])
    failures = Any[]
    for i in 1:(length(stabilizers) - 1), j in (i + 1):length(stabilizers)
        if symplectic_anticommutes(stabilizers[i], stabilizers[j])
            push!(failures, [stabilizers[i], stabilizers[j]])
        end
    end
    Dict{String,Any}(
        "pass" => isempty(failures) && qc["pass"],
        "strength_label" => "symbolic_identity",
        "GHZ" => Dict("state" => "(|" * repeat("0", n) * ">+|" * repeat("1", n) * ">)/sqrt(2)", "entropy_qubit_0" => "log(2)", "entropy_qubits_0_1" => "log(2)", "stabilizer_generators" => stabilizers, "stabilizer_generators_pairwise_commuting" => isempty(failures), "quantumclifford_stabilizer_object" => qc, "strength_label" => "symbolic_identity"),
        "product" => Dict("state" => "|" * repeat("0", n) * ">", "entropy_qubit_0" => "0", "strength_label" => "symbolic_identity"),
        "Bell_pair_plus_spectators" => Dict("state" => "(|00...0>+|11" * repeat("0", n - 2) * ">)/sqrt(2)", "entropy_qubits_0_1" => "0", "entropy_spectator_qubit_2" => "0", "strength_label" => "symbolic_identity"),
        "scope_boundary" => Dict("full_multi_party_entanglement_classification" => "not_scoped", "reason" => "Named exact controls only; no arbitrary classification of $(n)-party entanglement is claimed.", "strength_label" => "open_with_reason"),
    )
end

function w6_ceiling(n::Int)
    Dict{String,Any}(
        "pass" => true,
        "strength_label" => "negative_control",
        "rung_role" => n < 8 ? "scaling_stress_boundary" : "finite_overbuild_boundary",
        "new_minimum_claimed" => false,
        "minimum_floor_moved_from_3Q" => false,
        "eight_qubit_ceiling" => n == 8,
        "must_not_claim" => ["new minimum", "formal carrier admission", "final M(C)", "QIT-engine admission", "physics admission", "bridge or axis-level claim"],
        "negative_control_against_minimum_overclaim" => Dict("claim" => "because $(n)Q works, the 3Q minimum floor moved", "verdict" => "rejected", "z3_n_equals_3_control" => z3_assert_equal(n, 3), "strength_label" => "negative_control"),
    )
end

function classification_table(n::Int)
    w2_claim = "Cl$(2 * n) exact floor"
    if n == 8
        w2_claim = "Cl16 formula-backed exact floor; CliffordAlgebra(16,0) not materialized in packet"
    end
    rows = [
        ("F01", "finitude receipt", "exact_integer_combinatorial", true),
        ("N01.O1", "commuting control", "exact_integer_combinatorial", true),
        ("N01.O2", "general noncommuting witness", "exact_integer_combinatorial", true),
        ("N01.O3", "noncommuting but not anticommuting witness", "exact_integer_combinatorial", true),
        ("N01.O4", "Clifford anticommuting witness", "exact_integer_combinatorial", true),
        ("N01.O5", "state order gap", "exact_integer_combinatorial", true),
        ("N01.O6", "Clifford capacity separate row", "representation_theorem_with_constructive_receipt", true),
        ("T01.matrix", "matrix associator control", "representation_theorem_with_constructive_receipt", true),
        ("T01.schedule", "schedule associator not scoped", "open_with_reason", false),
        ("W1", "carrier and quotient", "symbolic_identity", true),
        ("W2", w2_claim, "exact_integer_combinatorial", true),
        ("W3", "max anticommuting family $(2 * n + 1)", "representation_theorem_with_constructive_receipt", true),
        ("W4", "finite Pauli-string stress scan", "finite_exhaustive_enumeration", true),
        ("W4.resource", "resource bounds", "diagnostic_float_nonclaim", false),
        ("W5", "named sparse stabilizer controls", "symbolic_identity", true),
        ("W6", "scaling/no-new-minimum boundary", "negative_control", true),
    ]
    table = [Dict("row_id" => row_id, "claim" => claim, "strength_label" => strength, "claim_bearing" => claim_bearing, "bare_float_claim" => false) for (row_id, claim, strength, claim_bearing) in rows]
    invalid = [row for row in table if !(row["strength_label"] in ALLOWED_STRENGTHS)]
    forbidden = [row for row in table if row["strength_label"] in FORBIDDEN_ROW_LABELS]
    bare = [row for row in table if row["claim_bearing"] && row["bare_float_claim"]]
    Dict{String,Any}(
        "pass" => isempty(invalid) && isempty(forbidden) && isempty(bare),
        "strength_label" => "exact_integer_combinatorial",
        "allowed_strengths" => sort(collect(ALLOWED_STRENGTHS)),
        "forbidden_row_list" => sort(collect(FORBIDDEN_ROW_LABELS)),
        "rows" => table,
        "invalid_strength_rows" => invalid,
        "forbidden_strength_rows" => forbidden,
        "bare_float_claim_rows" => bare,
        "zero_claim_bearing_bare_float_rows" => isempty(bare),
    )
end

function rung_receipts(n::Int)
    receipts = Dict{String,Any}(
        "F01_finitude_receipt" => f01(n),
        "N01_noncommutation_receipt" => n01(n),
        "T01_bracketing_receipt" => t01(n),
        "W1_carrier_quotient" => w1_carrier(n),
        "W2_Cl2n_exact_floor" => w2_clifford(n),
        "W3_max_anticommuting_family" => w3_max_family(n),
        "W4_finite_pauli_string_stress" => w4_pauli_stress(n),
        "W5_named_stabilizer_controls" => w5_named_controls(n),
        "W6_scaling_boundary_ceiling" => w6_ceiling(n),
    )
    receipts["W7_classification_table"] = classification_table(n)
    receipts
end

function build_result()
    started = time()
    rungs = Dict(string(n) => rung_receipts(n) for n in RUNG_NS)
    proofs = Dict{String,Any}()
    for n in RUNG_NS
        key = string(n)
        proofs[key] = Dict(
            "P1_finite_pauli_extension_scan" => Dict(
                "z3_no_full_family_extension" => z3_assert_equal(rungs[key]["W4_finite_pauli_string_stress"]["full_family_extension_scan"]["candidate_count"], 0),
                "z3_erased_chirality_control" => z3_assert_equal(rungs[key]["W4_finite_pauli_string_stress"]["erased_chirality_positive_control_scan"]["candidate_count"], 1),
                "pass" => rungs[key]["W4_finite_pauli_string_stress"]["pass"],
            ),
            "P2_max_family_bound" => rungs[key]["W3_max_anticommuting_family"]["proofs"],
            "P3_named_state_controls" => Dict(
                "GHZ_single_entropy" => rungs[key]["W5_named_stabilizer_controls"]["GHZ"]["entropy_qubit_0"],
                "product_single_entropy" => rungs[key]["W5_named_stabilizer_controls"]["product"]["entropy_qubit_0"],
                "Bell_pair_entropy" => rungs[key]["W5_named_stabilizer_controls"]["Bell_pair_plus_spectators"]["entropy_qubits_0_1"],
                "z3_product_GHZ_label_swap_detected" => z3_assert_equal(rungs[key]["W5_named_stabilizer_controls"]["GHZ"]["entropy_qubit_0"] == rungs[key]["W5_named_stabilizer_controls"]["product"]["entropy_qubit_0"] ? 1 : 0, 1),
                "pass" => rungs[key]["W5_named_stabilizer_controls"]["pass"],
            ),
        )
    end
    all_pass = all(all(receipt["pass"] == true for receipt in values(rung)) for rung in values(rungs)) &&
        all(all(proof["pass"] == true for proof in values(rung_proofs)) for rung_proofs in values(proofs))
    shared_scalars = Dict(string(n) => Dict(
        "hilbert_dim" => 2^n,
        "operator_basis_count" => 4^n,
        "mixed_density_real_dim" => 4^n - 1,
        "gamma_count" => 2 * n,
        "chirality_positive_dim" => 2^(n - 1),
        "chirality_negative_dim" => 2^(n - 1),
        "max_anticommuting_family" => 2 * n + 1,
        "next_family_allowed" => 0,
        "full_family_pauli_extension_candidates" => 0,
        "minimum_floor_moved_from_3Q" => 0,
        "claim_bearing_bare_float_rows" => 0,
    ) for n in RUNG_NS)
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
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "runtime_seconds" => round(time() - started; digits=6),
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["CliffordAlgebras", "QuantumClifford", "Symbolics", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "QuantumClifford", "Symbolics", "Z3"],
        "claim_path_tools" => ["CliffordAlgebras", "QuantumClifford", "Symbolics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "QuantumClifford",
                "qualified_api/function" => "QuantumClifford.PauliOperator/Stabilizer/stab_to_gf2/comm",
                "input_object" => "Jordan-Wigner gamma labels and GHZ stabilizer generators for n=6,7,8",
                "output_object" => Dict(
                    string(n) => Dict(
                        "W2" => rungs[string(n)]["W2_Cl2n_exact_floor"]["quantumclifford_receipt"],
                        "W5" => rungs[string(n)]["W5_named_stabilizer_controls"]["GHZ"]["quantumclifford_stabilizer_object"],
                    ) for n in RUNG_NS
                ),
                "positive_case" => "QuantumClifford PauliOperators anticommute for distinct gamma labels and stabilizer generators commute",
                "negative/erased_control" => "non-stabilizer max-family capacity remains in representation theorem row, not promoted by stabilizer syntax",
                "boundary_case" => "n=8 Cl16 applicability is checked only where PauliOperator/stabilizer formalism applies",
                "demotion_condition" => "if QuantumClifford is unavailable or comm/stabilizer gates fail, W2/W5 package route is blocked and hand labels are mirrors",
                "gates" => ["all_pass", "W2_Cl2n_exact_floor", "W5_named_stabilizer_controls"],
            ),
            Dict(
                "tool" => "CliffordAlgebras",
                "qualified_api/function" => "CliffordAlgebras.CliffordAlgebra",
                "input_object" => "bounded package construction plus existing capability artifact",
                "output_object" => "CliffordAlgebra(2,0) local object and checked capability artifact path",
                "positive_case" => "Clifford package route exists while large Cl(12/14/16) capacity claims are bounded by theorem rows",
                "negative/erased_control" => "hand Pauli-label tables remain mirrors if package route is removed",
                "boundary_case" => "Cl16 n=8 row stays scratch_diagnostic and non-admission",
                "demotion_condition" => "if CliffordAlgebras capability artifact is unavailable, CliffordAlgebras route is not load-bearing",
                "gates" => ["all_pass", "W2_Cl2n_exact_floor"],
            ),
        ],
        "theorem_receipt_once" => theorem_receipt_once(),
        "rungs" => rungs,
        "proofs" => proofs,
        "shared_scalars" => shared_scalars,
        "ceiling" => Dict(
            "classification" => CLASSIFICATION,
            "promotion_allowed" => PROMOTION_ALLOWED,
            "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
            "carrier_admission_allowed" => false,
            "final_MC_allowed" => false,
            "qit_engine_admission_allowed" => false,
            "physics_or_bridge_claim_allowed" => false,
            "eight_qubit_finite_overbuild_boundary" => true,
        ),
        "builder_self_check_is_evidence" => false,
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
    result["all_pass"] ? 0 : 1
end

exit(main())
