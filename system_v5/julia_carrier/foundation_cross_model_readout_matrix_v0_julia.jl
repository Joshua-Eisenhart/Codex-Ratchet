#!/usr/bin/env julia
# object_id: foundation_cross_model_readout_matrix_v0_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using SHA
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras

const RUNG_ID = "cross_model_readout_matrix_v0"
const OBJECT_ID = "foundation_cross_model_readout_matrix_v0_julia"
const ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_cross_model_readout_matrix_v0_julia_results.json")
const CARRIER_SOURCE_PATH = joinpath(ROOT, "system_v5", "ops", "formal_scouts", "sim_three_engine_clifford_spinor_carrier_envelope.py")
const CARRIER_RESULT_PATH = joinpath(ROOT, "system_v5", "ops", "formal_scouts", "results", "three_engine_clifford_spinor_carrier_envelope_results.json")
const TOL = 1.0e-9

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const BASIS_LABELS = ["uuu", "duu", "udu", "ddu", "uud", "dud", "udd", "ddd"]
const LENS_ORDER = ["qit", "igt", "holodeck_runtime", "physics_math"]
const LABEL_SHUFFLE_ORDER = ["igt", "physics_math", "qit", "holodeck_runtime"]

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing construction of carrier density operators plus von Neumann and subsystem entropy readouts",
    ),
    "CliffordAlgebras" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Clifford grade-vector content for the physics/math readout column",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive trace, eigenvalue, and matrix hygiene checks; not the carrier authority",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization",
    ),
    "SHA" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive source fingerprint",
    ),
    "Dates" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive UTC timestamp",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "Dates" => "supportive",
)

function sha256_file(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function support_vectors()
    states = Vector{Dict{String,Any}}()

    basis_uuu = zeros(ComplexF64, 8)
    basis_uuu[1] = 1.0 + 0.0im
    push!(states, Dict{String,Any}(
        "state_id" => "basis_uuu",
        "description" => "Cl(6) spinor basis density at |uuu>",
        "amplitudes" => basis_uuu,
    ))

    ghz = zeros(ComplexF64, 8)
    ghz[1] = 1 / sqrt(2)
    ghz[8] = 1 / sqrt(2)
    push!(states, Dict{String,Any}(
        "state_id" => "ghz_phase",
        "description" => "two-corner coherent spinor density over |uuu> and |ddd>",
        "amplitudes" => ghz,
    ))

    w_state = zeros(ComplexF64, 8)
    w_state[2] = 1 / sqrt(3)
    w_state[3] = 1 / sqrt(3)
    w_state[5] = 1 / sqrt(3)
    push!(states, Dict{String,Any}(
        "state_id" => "w_single_down",
        "description" => "single-down W spinor density over |duu>, |udu>, |uud>",
        "amplitudes" => w_state,
    ))

    biased = zeros(ComplexF64, 8)
    biased[1] = sqrt(1 / 2)
    biased[4] = sqrt(1 / 4)
    biased[6] = im * sqrt(1 / 8)
    biased[7] = sqrt(1 / 8)
    push!(states, Dict{String,Any}(
        "state_id" => "biased_phase",
        "description" => "asymmetric phase spinor density with rational diagonal support",
        "amplitudes" => biased,
    ))

    states
end

function density_from_vector(basis, vec::Vector{ComplexF64})
    ket = Ket(basis, vec)
    dm(ket)
end

function erased_density(basis)
    Operator(basis, basis, Matrix{ComplexF64}(I, 8, 8) / 8)
end

function complex_pairs(vec::Vector{ComplexF64})
    [Dict{String,Float64}("real" => real(v), "imag" => imag(v)) for v in vec]
end

function diag_probs(mat)
    [Float64(real(mat[idx, idx])) for idx in 1:size(mat, 1)]
end

function bit_sign(index0::Int, qubit::Int)
    bit = (index0 >> qubit) & 1
    bit == 0 ? 1.0 : -1.0
end

function z_expectations_from_diag(diag::Vector{Float64})
    [sum(bit_sign(idx - 1, qubit) * diag[idx] for idx in 1:8) for qubit in 0:2]
end

function pauli_coord(rho::Matrix{ComplexF64}, qubit::Int, pauli::String)
    total = 0.0 + 0.0im
    for rest in 0:3
        lower = rest & ((1 << qubit) - 1)
        upper = rest >> qubit
        idx0 = lower | (0 << qubit) | (upper << (qubit + 1))
        idx1 = lower | (1 << qubit) | (upper << (qubit + 1))
        a = idx0 + 1
        b = idx1 + 1
        if pauli == "X"
            total += rho[a, b] + rho[b, a]
        elseif pauli == "Y"
            total += -im * rho[a, b] + im * rho[b, a]
        else
            error("unsupported pauli $pauli")
        end
    end
    Float64(real(total))
end

function qit_readout(rho_op)
    mat = Matrix{ComplexF64}(rho_op.data)
    reduced_q0 = ptrace(rho_op, [2, 3])
    Dict{String,Any}(
        "von_neumann_entropy" => Float64(real(entropy_vn(rho_op))),
        "coherence_l1" => Float64(sum(abs(mat[i, j]) for i in 1:8, j in 1:8 if i != j)),
        "purity" => Float64(real(tr(mat * mat))),
        "subsystem_entropy_q0" => Float64(real(entropy_vn(reduced_q0))),
    )
end

function igt_readout(mat::Matrix{ComplexF64})
    z = z_expectations_from_diag(diag_probs(mat))
    asym = [abs(z[1] - z[2]), abs(z[1] - z[3]), abs(z[2] - z[3])]
    Dict{String,Any}(
        "observable" => "win_lose_payoff_asymmetry_only",
        "payoff_definition" => "P[i,j]=max(0, z_i-z_j); report abs(P[i,j]-P[j,i]) == abs(z_i-z_j)",
        "z_expectations" => z,
        "asymmetry_pairs" => Dict{String,Float64}(
            "q0_q1" => asym[1],
            "q0_q2" => asym[2],
            "q1_q2" => asym[3],
        ),
        "asymmetry_sum" => Float64(sum(asym)),
    )
end

function holodeck_signature(diag::Vector{Float64})
    acc = 3
    seen = Set{Int}()
    path_sum = 0
    threshold_step = length(diag)
    found_threshold = false
    for idx in 1:length(diag)
        bucket = Int(round(1000 * diag[idx]))
        acc = mod(acc * 5 + bucket + (idx - 1), 97)
        push!(seen, acc)
        path_sum += idx * acc
        if !found_threshold && mod(acc, 11) == 0
            threshold_step = idx
            found_threshold = true
        end
    end
    Dict{String,Any}(
        "ordered_basis" => BASIS_LABELS,
        "final_accumulator_mod97" => acc,
        "unique_runtime_states" => length(seen),
        "threshold_step_mod11_zero" => threshold_step,
        "weighted_path_sum" => path_sum,
        "normalized_signature" => [
            acc / 96,
            length(seen) / 8,
            threshold_step / 8,
            path_sum / (96 * sum(1:8)),
        ],
    )
end

function physics_readout(mat::Matrix{ComplexF64})
    x0 = pauli_coord(mat, 0, "X")
    y0 = pauli_coord(mat, 0, "Y")
    z0 = z_expectations_from_diag(diag_probs(mat))[1]
    cl3 = CliffordAlgebra(3, 0)
    grade_vector = x0 * cl3.e1 + y0 * cl3.e2 + z0 * cl3.e3
    grade1_norm = Float64(CliffordAlgebras.norm(grade_vector))
    Dict{String,Any}(
        "coordinate_source" => "first-qubit Pauli coordinates read as Cl(3,0) grade-1 vector",
        "pauli_x_q0" => x0,
        "pauli_y_q0" => y0,
        "pauli_z_q0" => z0,
        "clifford_grade1_norm" => grade1_norm,
        "density_frobenius_norm" => Float64(sqrt(real(tr(mat * mat)))),
    )
end

function scalar_profile(readouts::Dict{String,Any})
    qit = readouts["qit"]
    igt = readouts["igt"]
    hol = readouts["holodeck_runtime"]
    phy = readouts["physics_math"]
    Dict{String,Float64}(
        "qit" => qit["von_neumann_entropy"] + qit["coherence_l1"] + qit["purity"] + qit["subsystem_entropy_q0"],
        "igt" => igt["asymmetry_sum"],
        "holodeck_runtime" => sum(Float64.(hol["normalized_signature"])),
        "physics_math" => abs(phy["pauli_x_q0"]) + abs(phy["pauli_y_q0"]) + abs(phy["pauli_z_q0"]) + phy["clifford_grade1_norm"],
    )
end

function matrix_from_profiles(profiles::Vector{Dict{String,Float64}}, order::Vector{String})
    [[profile[lens] for lens in order] for profile in profiles]
end

function matrix_l1_delta(left, right)
    total = 0.0
    for i in eachindex(left), j in eachindex(left[i])
        total += abs(left[i][j] - right[i][j])
    end
    total
end

function column_std_sum(matrix)
    rows = length(matrix)
    cols = length(matrix[1])
    total = 0.0
    for col in 1:cols
        vals = [matrix[row][col] for row in 1:rows]
        mean_val = sum(vals) / rows
        total += sqrt(sum((v - mean_val)^2 for v in vals) / rows)
    end
    total
end

function rounded_signature(profile::Dict{String,Float64})
    [round(profile[lens]; digits=9) for lens in LENS_ORDER]
end

function class_count(profiles::Vector{Dict{String,Float64}})
    length(Set([JSON.json(rounded_signature(profile)) for profile in profiles]))
end

function constraints_for_density(mat::Matrix{ComplexF64})
    eigs = eigvals(Hermitian(mat))
    Dict{String,Any}(
        "trace_eq_1" => abs(real(tr(mat)) - 1.0) <= TOL,
        "psd" => minimum(real.(eigs)) >= -TOL,
        "hermitian" => norm(mat - mat') <= TOL,
        "normalization" => abs(real(tr(mat)) - 1.0) <= TOL,
        "min_eigenvalue" => Float64(minimum(real.(eigs))),
    )
end

function compute_rows(; erased::Bool=false, reversed_order::Bool=false)
    qb = SpinBasis(1 // 2)
    basis = tensor(qb, qb, qb)
    rows = Vector{Dict{String,Any}}()
    profiles = Vector{Dict{String,Float64}}()
    constraints = Vector{Dict{String,Any}}()
    states = support_vectors()

    for state in states
        rho_op = erased ? erased_density(basis) : density_from_vector(basis, state["amplitudes"])
        mat = Matrix{ComplexF64}(rho_op.data)
        diag = diag_probs(mat)
        if reversed_order
            diag = reverse(diag)
        end
        readouts = Dict{String,Any}(
            "qit" => qit_readout(rho_op),
            "igt" => igt_readout(mat),
            "holodeck_runtime" => holodeck_signature(diag),
            "physics_math" => physics_readout(mat),
        )
        profile = scalar_profile(readouts)
        push!(profiles, profile)
        push!(constraints, constraints_for_density(mat))
        push!(rows, Dict{String,Any}(
            "state_id" => state["state_id"],
            "support_index_labels" => BASIS_LABELS,
            "amplitudes" => erased ? "maximally_mixed_density_no_spinor_amplitudes" : complex_pairs(state["amplitudes"]),
            "readouts" => readouts,
            "scalar_profile" => profile,
            "constraints" => constraints[end],
        ))
    end
    rows, profiles, constraints
end

function build_result()
    started = time()
    rows, profiles, constraints = compute_rows()
    erased_rows, erased_profiles, erased_constraints = compute_rows(erased=true)
    reversed_rows, reversed_profiles, _ = compute_rows(reversed_order=true)

    matrix = matrix_from_profiles(profiles, LENS_ORDER)
    shuffled_matrix = matrix_from_profiles(profiles, LABEL_SHUFFLE_ORDER)
    erased_matrix = matrix_from_profiles(erased_profiles, LENS_ORDER)
    reversed_matrix = matrix_from_profiles(reversed_profiles, LENS_ORDER)
    igt_erased_profiles = [merge(profile, Dict("igt" => 0.0)) for profile in profiles]
    igt_erased_matrix = matrix_from_profiles(igt_erased_profiles, LENS_ORDER)

    label_delta = matrix_l1_delta(matrix, shuffled_matrix)
    real_structure = column_std_sum(matrix)
    erased_structure = column_std_sum(erased_matrix)
    map_before = column_std_sum([[row[2]] for row in matrix])
    map_after = column_std_sum([[row[2]] for row in igt_erased_matrix])
    order_delta = matrix_l1_delta(matrix, reversed_matrix)

    full_classes = class_count(profiles)
    erased_classes = class_count(erased_profiles)

    all_constraints_ok = all(c["trace_eq_1"] && c["psd"] && c["hermitian"] && c["normalization"] for c in constraints)
    controls_ok = label_delta > TOL &&
                  real_structure > TOL &&
                  erased_structure <= TOL &&
                  map_before > TOL &&
                  map_after <= TOL &&
                  order_delta > TOL &&
                  full_classes > erased_classes

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "backend" => "julia_authoritative_quantumoptics_cliffordalgebras",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "ran" => true,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "result_path" => RESULT_PATH,
        "carrier_source_pin" => Dict{String,Any}(
            "source_path" => CARRIER_SOURCE_PATH,
            "result_path" => CARRIER_RESULT_PATH,
            "read_only" => true,
            "rebuilt" => false,
        ),
        "claim_ceiling" => "Scratch diagnostic cross-model readout matrix only: four readout lenses over one fixed Clifford-spinor support S. No identity, canon, bridge, IGT truth, physics truth, Axis0, or formal admission claim.",
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras"],
        "package_table" => TOOL_MANIFEST,
        "M" => Dict{String,Any}(
            "explicit_finite_probe_family" => [
                "QIT: von Neumann entropy, l1 coherence, purity, first-qubit subsystem entropy",
                "IGT lens only: abs(P[i,j]-P[j,i]) over qubit-Z payoff probes derived from carrier density",
                "Holodeck/runtime: ordered diagonal trajectory accumulator/reachability signature",
                "Physics/math: Cl(3,0) grade-1 vector content from first-qubit Pauli coordinates",
            ],
            "matrix_shape" => [length(rows), length(LENS_ORDER)],
            "lens_order" => LENS_ORDER,
        ),
        "C" => Dict{String,Any}(
            "trace_eq_1" => all(c["trace_eq_1"] for c in constraints),
            "psd" => all(c["psd"] for c in constraints),
            "hermitian" => all(c["hermitian"] for c in constraints),
            "normalization" => all(c["normalization"] for c in constraints),
            "rung_specific_constraint" => "All four readout maps consume the same fixed support S of four Cl(6)-spinor density states; no readout consumes another readout and no lens identity is asserted.",
        ),
        "S_mod_M" => Dict{String,Any}(
            "S" => [row["state_id"] for row in rows],
            "equivalence_relation" => "s ~_M t iff every scalarized readout probe in the four-lens matrix agrees after rounding to 1e-9",
            "full_probe_class_count" => full_classes,
            "carrier_erased_class_count" => erased_classes,
            "full_signatures" => [rounded_signature(profile) for profile in profiles],
            "carrier_erased_signatures" => [rounded_signature(profile) for profile in erased_profiles],
        ),
        "readout_rows" => rows,
        "control_rows" => Dict{String,Any}(
            "carrier_erasure_rows" => erased_rows,
            "order_reversal_rows" => reversed_rows,
        ),
        "controls" => Dict{String,Any}(
            "label_shuffle" => Dict{String,Any}(
                "falsifies" => "Rosetta-style relabeling where all lenses carry the same chart",
                "original_lens_order" => LENS_ORDER,
                "shuffled_lens_order" => LABEL_SHUFFLE_ORDER,
                "matrix_l1_delta" => label_delta,
                "flips" => label_delta > TOL,
            ),
            "carrier_erasure" => Dict{String,Any}(
                "falsifies" => "carrier-agnostic decorative readouts",
                "real_structure_norm" => real_structure,
                "erased_structure_norm" => erased_structure,
                "structure_drop" => real_structure - erased_structure,
                "full_class_count" => full_classes,
                "erased_class_count" => erased_classes,
                "flips" => real_structure > TOL && erased_structure <= TOL && full_classes > erased_classes,
            ),
            "readout_map_erasure" => Dict{String,Any}(
                "falsifies" => "a readout column that remains structured after replacing A_i with a constant map",
                "erased_lens" => "igt",
                "column_structure_before" => map_before,
                "column_structure_after" => map_after,
                "flips" => map_before > TOL && map_after <= TOL,
            ),
            "order_composition_reversal" => Dict{String,Any}(
                "falsifies" => "runtime readout ignoring its ordered carrier composition",
                "basis_order" => BASIS_LABELS,
                "reversed_basis_order" => reverse(BASIS_LABELS),
                "matrix_l1_delta" => order_delta,
                "flips" => order_delta > TOL,
            ),
        ),
        "summary" => Dict{String,Any}(
            "support_size" => length(rows),
            "lens_count" => length(LENS_ORDER),
            "full_probe_class_count" => full_classes,
            "carrier_erased_class_count" => erased_classes,
            "label_shuffle_delta" => label_delta,
            "real_structure_norm" => real_structure,
            "erased_structure_norm" => erased_structure,
            "readout_map_erasure_before" => map_before,
            "readout_map_erasure_after" => map_after,
            "order_reversal_delta" => order_delta,
            "all_constraints_ok" => all_constraints_ok,
        ),
        "all_pass" => all_constraints_ok && controls_ok,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_seconds" => round(time() - started; digits=6),
    )
end

function main()
    mkpath(dirname(RESULT_PATH))
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    summary = result["summary"]
    println("wrote: $(RESULT_PATH)")
    println(
        "CROSS_MODEL_READOUT_MATRIX_V0_JULIA_DONE " *
        "all_pass=$(result["all_pass"]) " *
        "classes=$(summary["full_probe_class_count"])->$(summary["carrier_erased_class_count"]) " *
        "label_delta=$(summary["label_shuffle_delta"]) " *
        "erased_structure=$(summary["erased_structure_norm"]) " *
        "order_delta=$(summary["order_reversal_delta"])",
    )
end

main()
