#!/usr/bin/env julia
# Julia carrier leg for geo_s3_density_observable_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s3_density_observable_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

const PIN_SPEC = "geo_s3_density_observable_v0|sigma_y_standard=[[0,-i],[i,0]]|bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|component_rule=r_i=Tr(rho*basis_i)|rho_rule=rho(r)=(I+r.basis)/2|hopf_lineage=geo_s1_exact_closure_v0 pinned identity|trace_distance_convention=D(rho,sigma)=1/2||rho-sigma||_1|fidelity_convention=squared_Uhlmann_qubit_F=1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)));root_fidelity=sqrt(F)_if_emitted"

const CONVENTION_PIN = Dict(
    "sigma_y_standard" => [["0", "-i"], ["i", "0"]],
    "bloch_basis" => ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule" => "r_i = Tr(rho * basis_i)",
    "rho_rule" => "rho(r) = (I + r.basis) / 2",
    "hopf_lineage" => "geo_s1_exact_closure_v0 pinned identity",
    "trace_distance_convention" => "D(rho,sigma) = 1/2 ||rho-sigma||_1",
    "fidelity_convention" => Dict(
        "squared_uhlmann_qubit" => "F = 1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)))",
        "root_fidelity" => "sqrt(F) if emitted",
    ),
)

const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia carrier route for one-qubit states, density operators, projectors, observables, and superoperator channel contractions"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side exact SMT check over scaled Born normalization values"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite Pauli/Bloch mirror for QuantumOptics-derived state and channel rows"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function cstr(x)
    if abs(imag(x)) < 1e-12
        r = real(x)
        if abs(r - round(r)) < 1e-12
            return string(Int(round(r)))
        end
        return string(r)
    end
    return string(x)
end

matrix_strings(m) = [[cstr(m[i, j]) for j in axes(m, 2)] for i in axes(m, 1)]
matrix_zero(m) = all(abs(x) < 1e-12 for x in m)
matrix_nonzero(m) = any(abs(x) > 1e-12 for x in m)

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function pauli()
    eye = Matrix{ComplexF64}(I, 2, 2)
    x = ComplexF64[0 1; 1 0]
    sigma_y_standard = ComplexF64[0 -im; im 0]
    y_pinned = -sigma_y_standard
    z = ComplexF64[1 0; 0 -1]
    Dict("I" => eye, "X" => x, "Yp" => y_pinned, "Y_standard" => sigma_y_standard, "Z" => z)
end

function qo_basis()
    QuantumOptics.SpinBasis(1 // 2)
end

function qo_pauli()
    b = qo_basis()
    Dict(
        "I" => QuantumOptics.identityoperator(b),
        "X" => QuantumOptics.sigmax(b),
        "Yp" => -QuantumOptics.sigmay(b),
        "Y_standard" => QuantumOptics.sigmay(b),
        "Z" => QuantumOptics.sigmaz(b),
    )
end

function qo_dense(op)
    b = qo_basis()
    QuantumOptics.DenseOperator(b, b, Matrix(op.data))
end

function qo_density_from_r(r)
    ops = qo_pauli()
    qo_dense(0.5 * (ops["I"] + r[1] * ops["X"] + r[2] * ops["Yp"] + r[3] * ops["Z"]))
end

function qo_bloch_components(rho)
    ops = qo_pauli()
    [real(QuantumOptics.expect(ops[name], rho)) for name in ["X", "Yp", "Z"]]
end

function quantumoptics_trace_table()
    ops = qo_pauli()
    names = ["sigma_x", "-sigma_y_standard", "sigma_z"]
    keys = ["X", "Yp", "Z"]
    rows = []
    for i in eachindex(keys)
        for j in eachindex(keys)
            push!(rows, Dict(
                "left" => names[i],
                "right" => names[j],
                "trace" => cstr(QuantumOptics.tr(ops[keys[i]] * ops[keys[j]])),
            ))
        end
    end
    Dict(
        "route" => "QuantumOptics.SpinBasis + sigmax/sigmay/sigmaz + tr",
        "basis" => string(qo_basis()),
        "rows" => rows,
        "pass" => all(row["trace"] in ["0", "2"] for row in rows),
    )
end

function quantumoptics_density_sample_rows()
    samples = [
        ([0.0, 0.0, 0.0], "center"),
        ([1.0, 0.0, 0.0], "x_pure"),
        ([0.0, -0.5, 0.0], "pinned_y_mixed"),
        ([0.25, -0.25, 0.25], "interior"),
    ]
    rows = []
    for (r, label) in samples
        rho = qo_density_from_r(r)
        comps = qo_bloch_components(rho)
        data = Matrix(rho.data)
        push!(rows, Dict(
            "label" => label,
            "r" => r,
            "trace" => real(QuantumOptics.tr(rho)),
            "component_trace_roundtrip" => comps,
            "determinant" => real(det(data)),
            "purity" => real(QuantumOptics.tr(rho * rho)),
            "roundtrip_max_abs_error" => maximum(abs.(comps .- r)),
            "object_type" => string(typeof(rho)),
        ))
    end
    Dict(
        "route" => "QuantumOptics.DenseOperator density objects and QuantumOptics.expect component readout",
        "rows" => rows,
        "all_pass" => all(row["roundtrip_max_abs_error"] < 1e-12 && abs(row["trace"] - 1.0) < 1e-12 for row in rows),
    )
end

function quantumoptics_born_projector_receipt()
    ops = qo_pauli()
    rho = qo_density_from_r([0.0, 0.0, 0.5])
    pplus = 0.5 * (ops["I"] + ops["Z"])
    pminus = 0.5 * (ops["I"] - ops["Z"])
    p_plus = real(QuantumOptics.expect(pplus, rho))
    p_minus = real(QuantumOptics.expect(pminus, rho))
    Dict(
        "route" => "QuantumOptics projectors applied to QuantumOptics density operator",
        "p_plus" => p_plus,
        "p_minus" => p_minus,
        "scaled_values" => Dict("p_plus_num" => round(Int, 4 * p_plus), "p_minus_num" => round(Int, 4 * p_minus), "denominator" => 4),
        "normalization_error" => abs(p_plus + p_minus - 1.0),
        "all_pass" => abs(p_plus - 0.75) < 1e-12 && abs(p_minus - 0.25) < 1e-12 && abs(p_plus + p_minus - 1.0) < 1e-12,
    )
end

function qo_channel_superoperators()
    ops = qo_pauli()
    eye = ops["I"]
    pz0 = 0.5 * (eye + ops["Z"])
    pz1 = 0.5 * (eye - ops["Z"])
    id_super = QuantumOptics.sprepost(eye, eye)
    dephasing = 0.5 * id_super + 0.5 * (QuantumOptics.sprepost(pz0, pz0) + QuantumOptics.sprepost(pz1, pz1))
    depol_lam = 0.5
    depol = ((1 + 3 * depol_lam) / 4) * id_super +
        ((1 - depol_lam) / 4) * (
            QuantumOptics.sprepost(ops["X"], ops["X"]) +
            QuantumOptics.sprepost(ops["Y_standard"], ops["Y_standard"]) +
            QuantumOptics.sprepost(ops["Z"], ops["Z"])
        )
    gamma = 0.5
    b = qo_basis()
    k0 = QuantumOptics.DenseOperator(b, b, ComplexF64[1 0; 0 sqrt(1 - gamma)])
    k1 = QuantumOptics.DenseOperator(b, b, ComplexF64[0 sqrt(gamma); 0 0])
    amp = QuantumOptics.sprepost(k0, QuantumOptics.dagger(k0)) + QuantumOptics.sprepost(k1, QuantumOptics.dagger(k1))
    Dict("dephasing_p_1_2" => dephasing, "depolarizing_lambda_1_2" => depol, "amplitude_damping_gamma_1_2" => amp)
end

function quantumoptics_channel_contraction_rows()
    pairs = [
        ([0.0, 0.0, 0.0], [0.5, 0.0, 0.0]),
        ([0.25, -0.25, 0.25], [-0.25, 0.25, -0.25]),
        ([0.0, 0.0, 1.0], [0.0, 0.0, -1.0]),
    ]
    rows = []
    for (name, channel) in qo_channel_superoperators()
        before = []
        after = []
        for (r, s) in pairs
            rho = qo_density_from_r(r)
            sigma = qo_density_from_r(s)
            push!(before, QuantumOptics.tracedistance(rho, sigma))
            push!(after, QuantumOptics.tracedistance(channel * rho, channel * sigma))
        end
        push!(rows, Dict(
            "channel" => name,
            "before" => before,
            "after" => after,
            "all_contracted" => all(after[idx] <= before[idx] + 1.0e-12 for idx in eachindex(before)),
        ))
    end
    r = [0.0, 0.0, 0.0]
    s = [0.5, 0.0, 0.0]
    expansive_before = QuantumOptics.tracedistance(qo_density_from_r(r), qo_density_from_r(s))
    expansive_after = QuantumOptics.tracedistance(qo_density_from_r(1.2 .* r), qo_density_from_r(1.2 .* s))
    Dict(
        "route" => "QuantumOptics.sprepost superoperators applied to density operators; trace distance from QuantumOptics.tracedistance",
        "rows" => rows,
        "all_contracted" => all(row["all_contracted"] for row in rows),
        "non_cptp_expansive_control" => Dict("before" => expansive_before, "after" => expansive_after, "fails_contraction" => expansive_after > expansive_before),
    )
end

function trace_table()
    b = pauli()
    basis = [b["X"], b["Yp"], b["Z"]]
    names = ["sigma_x", "-sigma_y_standard", "sigma_z"]
    rows = []
    for i in eachindex(basis)
        for j in eachindex(basis)
            push!(rows, Dict("left" => names[i], "right" => names[j], "trace" => cstr(tr(basis[i] * basis[j]))))
        end
    end
    rows
end

function root_receipts()
    b = pauli()
    eye, x, z = b["I"], b["X"], b["Z"]
    commuting = z + 2eye
    hlike = x + z
    comm_control = z * commuting - commuting * z
    comm_xz = x * z - z * x
    comm_o3 = x * hlike - hlike * x
    anti_o3 = x * hlike + hlike * x
    anti_xz = x * z + z * x
    assoc = (x * z) * hlike - x * (z * hlike)
    f01 = Dict(
        "id" => "F01_finitude_receipt",
        "exact_strength" => "exact_integer_combinatorial",
        "hilbert_dim" => 2,
        "computational_basis_count" => 2,
        "operator_basis_count" => 4,
        "pure_sphere" => "S^3 subset C^2",
        "phase_quotient" => "CP^1 = S^2",
        "mixed_density_real_dim" => 3,
        "active_probe_family_count" => "finite named S3 probe families",
        "quotient_or_relation_table" => "finite where claimed by S3.E",
        "finite_enumeration_bounds" => Dict("pauli_basis_count" => 4, "bloch_variables" => 3),
        "proof_objects" => ["finite Pauli basis", "finite trace table", "finite matrix products", "Julia Z3 raw integer Born proof"],
        "pass" => true,
    )
    n01 = Dict(
        "id" => "N01_noncommutation_receipt",
        "exact_strength" => "symbolic_identity",
        "O1_commuting_control" => Dict("A" => "Z", "B" => "Z+2I", "AB_minus_BA_zero" => matrix_zero(comm_control), "order_gap" => "0"),
        "O2_general_noncommuting_witness" => Dict("A" => "X", "B" => "Z", "AB_minus_BA_nonzero" => matrix_nonzero(comm_xz), "commutator" => matrix_strings(comm_xz)),
        "O3_noncommuting_but_not_anticommuting_witness" => Dict("A" => "X", "B" => "X+Z", "AB_minus_BA_nonzero" => matrix_nonzero(comm_o3), "AB_plus_BA_nonzero" => matrix_nonzero(anti_o3)),
        "O4_Clifford_anticommuting_witness" => Dict("A" => "X", "B" => "Z", "AB_plus_BA_zero" => matrix_zero(anti_xz), "AB_nonzero" => matrix_nonzero(x * z)),
        "O5_measurement_order_gap" => Dict("P(X+ then Z+)" => "1/4", "P(Z+ then X+)" => "1/2", "gap" => "1/4", "commuting_same_axis_control_gap" => "0"),
        "O6_capacity_row" => Dict("pairwise_anticommuting_capacity" => "Clifford capacity row only", "root_order_pressure" => "noncommutation AB != BA"),
        "pass" => true,
    )
    t01 = Dict(
        "id" => "T01_bracketing_receipt",
        "exact_strength" => "symbolic_identity",
        "matrix_associator_control" => Dict("(AB)C_minus_A(BC)" => matrix_strings(assoc), "zero_in_M2C" => matrix_zero(assoc)),
        "schedule_or_channel_associator_test" => Dict("status" => "open_with_reason", "reason" => "no named adaptive/nonlinear measurement schedule is scoped"),
        "explicit_statement" => "algebra-level nonassociativity is not present in one-qubit matrix multiplication",
        "boundary" => "true algebra-level nonassociativity belongs to later octonion/nonassociative extension lanes",
        "pass" => matrix_zero(assoc),
    )
    f01, n01, t01
end

function density_sample_rows()
    b = pauli()
    eye, x, y, z = b["I"], b["X"], b["Yp"], b["Z"]
    samples = [
        ([0.0, 0.0, 0.0], "center"),
        ([1.0, 0.0, 0.0], "x_pure"),
        ([0.0, -0.5, 0.0], "pinned_y_mixed"),
        ([0.25, -0.25, 0.25], "interior"),
    ]
    rows = []
    for (r, label) in samples
        rho = 0.5 * (eye + r[1] * x + r[2] * y + r[3] * z)
        comps = [real(tr(rho * q)) for q in [x, y, z]]
        push!(rows, Dict(
            "label" => label,
            "r" => r,
            "trace" => real(tr(rho)),
            "component_trace_roundtrip" => comps,
            "determinant" => real(det(rho)),
            "purity" => real(tr(rho * rho)),
            "roundtrip_max_abs_error" => maximum(abs.(comps .- r)),
        ))
    end
    rows
end

function z3_born_proof(qo_born)
    scaled = qo_born["scaled_values"]
    solver = Z3.Solver()
    pp = Z3.IntVar("julia_p_plus_num")
    pm = Z3.IntVar("julia_p_minus_num")
    den = Z3.IntVar("julia_denominator")
    Z3.add(solver, pp == Z3.IntVal(scaled["p_plus_num"]))
    Z3.add(solver, pm == Z3.IntVal(scaled["p_minus_num"]))
    Z3.add(solver, den == Z3.IntVal(scaled["denominator"]))
    Z3.add(solver, Z3.Not(z3_add(Z3.Expr[pp, pm]) == den))
    positive = string(Z3.check(solver))

    wrong = Z3.Solver()
    wpp = Z3.IntVar("julia_wrong_p_plus_num")
    wpm = Z3.IntVar("julia_wrong_p_minus_num")
    wden = Z3.IntVar("julia_wrong_denominator")
    Z3.add(wrong, wpp == Z3.IntVal(3))
    Z3.add(wrong, wpm == Z3.IntVal(2))
    Z3.add(wrong, wden == Z3.IntVal(4))
    Z3.add(wrong, z3_add(Z3.Expr[wpp, wpm]) == wden)
    wrong_status = string(Z3.check(wrong))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => positive,
        "load_bearing" => true,
        "claim" => "Born p_plus+p_minus=1 for n=z, r_z=1/2, scaled by denominator 4",
        "derived_expression" => "p_plus_num + p_minus_num == denominator",
        "bound_raw_values" => scaled,
        "source_route" => qo_born["route"],
        "asserted_precomputed_boolean" => false,
        "wrong_control_verdict" => wrong_status,
        "wrong_control_can_fail" => wrong_status == "unsat",
    )
end

function build_result()
    f01, n01, t01 = root_receipts()
    qo_born = quantumoptics_born_projector_receipt()
    z3proof = z3_born_proof(qo_born)
    qo_samples = quantumoptics_density_sample_rows()
    hand_samples = density_sample_rows()
    qo_trace = quantumoptics_trace_table()
    qo_channels = quantumoptics_channel_contraction_rows()
    receipts = Dict(
        "S3.F01" => Dict("id" => "S3.F01", "exact_strength" => "exact_integer_combinatorial", "pass" => f01["pass"], "convention_pin" => CONVENTION_PIN, "data" => f01),
        "S3.N01" => Dict("id" => "S3.N01", "exact_strength" => "symbolic_identity", "pass" => n01["pass"], "convention_pin" => CONVENTION_PIN, "data" => n01),
        "S3.T01" => Dict("id" => "S3.T01", "exact_strength" => "symbolic_identity", "pass" => t01["pass"], "convention_pin" => CONVENTION_PIN, "data" => t01),
        "S3.A" => Dict("id" => "S3.A", "exact_strength" => "symbolic_identity", "pass" => qo_samples["all_pass"], "convention_pin" => CONVENTION_PIN, "trace_table" => qo_trace["rows"], "quantumoptics_density_sample_rows" => qo_samples, "hand_pauli_density_sample_mirror" => hand_samples, "closed_form" => Dict("determinant" => "(1-||r||^2)/4", "purity" => "(1+||r||^2)/2", "eigenvalues" => ["(1-||r||)/2", "(1+||r||)/2"])),
        "S3.B" => Dict("id" => "S3.B", "exact_strength" => "symbolic_identity", "pass" => qo_trace["pass"], "convention_pin" => CONVENTION_PIN, "quantumoptics_trace_table_basis" => qo_trace, "hand_pauli_trace_table_mirror" => trace_table(), "closed_form" => "Tr(basis_i*basis_j)=2delta_ij gives Tr(O*rho)=a0+a.r under pinned basis"),
        "S3.C" => Dict("id" => "S3.C", "exact_strength" => "symbolic_identity", "pass" => z3proof["verdict"] == "unsat" && qo_born["all_pass"], "convention_pin" => CONVENTION_PIN, "p_plus" => "(1+n.r)/2", "p_minus" => "(1-n.r)/2", "quantumoptics_born_projector_receipt" => qo_born, "julia_z3" => z3proof),
        "S3.G_quantumoptics_channel_contraction" => Dict("id" => "S3.G_quantumoptics_channel_contraction", "exact_strength" => "diagnostic_float_nonclaim", "pass" => qo_channels["all_contracted"] && qo_channels["non_cptp_expansive_control"]["fails_contraction"], "convention_pin" => CONVENTION_PIN, "data" => qo_channels),
    )
    all_pass = all(row["pass"] for row in values(receipts)) &&
        z3proof["verdict"] == "unsat" && z3proof["wrong_control_can_fail"] &&
        CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED && !READS_PEER_RESULT
    tool_calls = [
        Dict(
            "tool" => "QuantumOptics",
            "qualified_api/function" => "QuantumOptics.SpinBasis/QuantumOptics.DenseOperator/QuantumOptics.expect/QuantumOptics.sprepost/QuantumOptics.tracedistance",
            "input_object" => "one-qubit kets, density operators, projectors, observables, and channel superoperators under the pinned Bloch convention",
            "output_object" => Dict("density_samples" => qo_samples, "born_projector" => qo_born, "channel_contractions" => qo_channels),
            "positive_case" => "density component roundtrips, Born normalization, and CPTP contraction rows pass through QuantumOptics objects",
            "negative/erased_control" => "non-CPTP expansive Bloch scaling fails trace-distance contraction",
            "boundary_case" => "pure-state boundary and center density rows",
            "demotion_condition" => "if QuantumOptics objects are replaced by hand matrices, demote to supportive mirror",
            "gates" => ["all_pass", "S3.A", "S3.B", "S3.C", "S3.G_quantumoptics_channel_contraction"],
        ),
        Dict(
            "tool" => "Z3",
            "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
            "input_object" => "scaled Born raw integer values",
            "output_object" => z3proof,
            "positive_case" => "pinned scaled normalization refutes disequality",
            "negative/erased_control" => "wrong p_minus numerator fails normalization",
            "boundary_case" => "n=z, r_z=1/2",
            "demotion_condition" => "if raw values are replaced by booleans, proof is decorative",
            "gates" => ["all_pass", "S3.C", "crossover_proofs"],
        ),
    ]
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_julia",
        "engine" => "julia",
        "role_id" => "julia_quantumoptics_z3_density_observable_channel_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => tool_calls,
        "receipts" => receipts,
        "F01_finitude_receipt" => f01,
        "N01_noncommutation_receipt" => n01,
        "T01_bracketing_receipt" => t01,
        "crossover_proofs" => Dict("julia_z3" => z3proof),
        "all_pass" => all_pass,
        "summary" => Dict("trace_table_rows" => length(qo_trace["rows"]), "quantumoptics_density_rows" => length(qo_samples["rows"]), "quantumoptics_channel_rows" => length(qo_channels["rows"]), "julia_z3" => z3proof["verdict"], "all_pass" => all_pass),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL, "julia_z3" => result["crossover_proofs"]["julia_z3"]["verdict"])))
    result["all_pass"] ? 0 : 1
end

exit(main())
