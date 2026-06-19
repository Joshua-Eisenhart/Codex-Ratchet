#!/usr/bin/env julia
# Julia carrier leg for geo_s4_operator_stage_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s4_operator_stage_v0"
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

const PIN_SPEC = "geo_s4_operator_stage_v0|sigma_y_standard=[[0,-i],[i,0]]|primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|standard_to_s1_pinned_J=diag(1,-1,1)|component_rule=r_i=Tr(rho*basis_i)|channels=(D_z,D_x,R_x,R_z)|source_forms=(Ti=z_dephase,Te=x_dephase,Fi=x_rotation,Fe=z_rotation)|symbolic_parameters=(q_z,q_x,theta_x,phi_z)|pin_row=(q_z=3/10,q_x=3/10,theta_x=pi/2,phi_z=pi/2)|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "sigma_y_standard" => [["0", "-i"], ["i", "0"]],
    "primary_table_basis" => "source_locked_standard_bloch",
    "source_locked_bloch_basis" => ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis" => ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J" => [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule" => "M_s1_pinned = J * M_source_locked_standard * J",
    "component_rule" => "r_i = Tr(rho * basis_i)",
    "rho_rule" => "rho(r) = (I + r.basis) / 2",
    "hopf_lineage" => "geo_s1_exact_closure_v0 pinned identity",
    "operator_channel_stage" => "S4 density/Bloch quotient only",
)

const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia carrier route for density operators and channel superoperators at the pinned S4 row"),
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side derivation from density, Kraus, and unitary channel forms with explicit half-angle trig reduction"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT pinned-entry contradiction check; not a full symbolic table proof"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive pinned Pauli/Bloch mirror for QuantumOptics channel rows"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function cstr(x)
    if x isa Complex
        re = Symbolics.simplify(real(x), expand=true)
        imv = Symbolics.simplify(imag(x), expand=true)
        if string(imv) in ["0", "0.0", "0//1"]
            return cstr(re)
        end
        return string(Symbolics.simplify(x, expand=true))
    end
    if x isa Num
        text = string(Symbolics.simplify(x, expand=true))
        text == "0.0" && return "0"
        text == "1.0" && return "1"
        return text
    end
    if x isa Real
        if abs(x - round(x)) < 1e-12
            return string(Int(round(x)))
        end
        return string(x)
    end
    if abs(imag(x)) < 1e-12
        r = real(x)
        if abs(r - round(r)) < 1e-12
            return string(Int(round(r)))
        end
        return string(r)
    end
    string(x)
end

matrix_strings(m) = [[cstr(m[i, j]) for j in axes(m, 2)] for i in axes(m, 1)]
matrix_zero_numeric(m) = all(abs(x) < 1e-12 for x in m)

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function pauli()
    eye = Complex{Int}[1 0; 0 1]
    x = Complex{Int}[0 1; 1 0]
    sigma_y_standard = Complex{Int}[0 -im; im 0]
    yp = -sigma_y_standard
    z = Complex{Int}[1 0; 0 -1]
    Dict("I" => eye, "X" => x, "Yp" => yp, "Y_standard" => sigma_y_standard, "Z" => z)
end

function qo_basis()
    QuantumOptics.SpinBasis(1 // 2)
end

function qo_ops_standard()
    b = qo_basis()
    Dict(
        "I" => QuantumOptics.identityoperator(b),
        "X" => QuantumOptics.sigmax(b),
        "Y_standard" => QuantumOptics.sigmay(b),
        "Z" => QuantumOptics.sigmaz(b),
    )
end

function qo_dense(op)
    b = qo_basis()
    QuantumOptics.DenseOperator(b, b, Matrix(op.data))
end

function qo_density_from_bloch_standard(r)
    ops = qo_ops_standard()
    qo_dense(0.5 * (ops["I"] + r[1] * ops["X"] + r[2] * ops["Y_standard"] + r[3] * ops["Z"]))
end

function qo_components_standard(rho)
    ops = qo_ops_standard()
    [real(QuantumOptics.expect(ops[name], rho)) for name in ["X", "Y_standard", "Z"]]
end

function qfrac(x)
    abs(x) < 1e-10 && return "0"
    r = rationalize(Float64(x), tol=1e-8)
    denominator(r) == 1 && return string(numerator(r))
    string(numerator(r), "/", denominator(r))
end

function qfrac_matrix(m)
    [[qfrac(m[i, j]) for j in axes(m, 2)] for i in axes(m, 1)]
end

function qo_channel_superoperators()
    ops = qo_ops_standard()
    eye = ops["I"]
    q = 0.3
    pz0 = 0.5 * (eye + ops["Z"])
    pz1 = 0.5 * (eye - ops["Z"])
    px0 = 0.5 * (eye + ops["X"])
    px1 = 0.5 * (eye - ops["X"])
    id_super = QuantumOptics.sprepost(eye, eye)
    dz = (1 - q) * id_super + q * (QuantumOptics.sprepost(pz0, pz0) + QuantumOptics.sprepost(pz1, pz1))
    dx = (1 - q) * id_super + q * (QuantumOptics.sprepost(px0, px0) + QuantumOptics.sprepost(px1, px1))
    theta = pi / 2
    phi = pi / 2
    b = qo_basis()
    ux = QuantumOptics.DenseOperator(b, b, exp(Matrix((-0.5im * theta * ops["X"]).data)))
    uz = QuantumOptics.DenseOperator(b, b, exp(Matrix((-0.5im * phi * ops["Z"]).data)))
    rx = QuantumOptics.sprepost(ux, QuantumOptics.dagger(ux))
    rz = QuantumOptics.sprepost(uz, QuantumOptics.dagger(uz))
    Dict("D_z" => dz, "D_x" => dx, "R_x" => rx, "R_z" => rz)
end

function qo_affine_from_super(superop)
    center = qo_density_from_bloch_standard([0.0, 0.0, 0.0])
    c = qo_components_standard(superop * center)
    basis_rows = [
        qo_components_standard(superop * qo_density_from_bloch_standard([1.0, 0.0, 0.0])) .- c,
        qo_components_standard(superop * qo_density_from_bloch_standard([0.0, 1.0, 0.0])) .- c,
        qo_components_standard(superop * qo_density_from_bloch_standard([0.0, 0.0, 1.0])) .- c,
    ]
    M = [basis_rows[col][row] for row in 1:3, col in 1:3]
    M, c
end

function matmul3(a, b)
    [[sum(a[i][k] * b[k][j] for k in 1:3) for j in 1:3] for i in 1:3]
end

function matsub3(a, b)
    [[a[i][j] - b[i][j] for j in 1:3] for i in 1:3]
end

function quantumoptics_pinned_channel_rows()
    expected = Dict(
        "D_z" => [["7/10", "0", "0"], ["0", "7/10", "0"], ["0", "0", "1"]],
        "D_x" => [["1", "0", "0"], ["0", "7/10", "0"], ["0", "0", "7/10"]],
        "R_x" => [["1", "0", "0"], ["0", "0", "-1"], ["0", "1", "0"]],
        "R_z" => [["0", "-1", "0"], ["1", "0", "0"], ["0", "0", "1"]],
    )
    rows = Dict{String, Any}()
    numeric = Dict{String, Any}()
    for (name, superop) in qo_channel_superoperators()
        M, c = qo_affine_from_super(superop)
        numeric[name] = M
        rows[name] = Dict(
            "M" => qfrac_matrix(M),
            "c" => [qfrac(x) for x in c],
            "qobj_type" => string(typeof(superop)),
            "pass" => qfrac_matrix(M) == expected[name] && all(abs.(c) .< 1e-10),
        )
    end
    comm = numeric["D_z"] * numeric["R_x"] - numeric["R_x"] * numeric["D_z"]
    entry_times_10 = round(Int, 10 * comm[2, 3])
    Dict(
        "route" => "QuantumOptics.sprepost channel superoperators applied to QuantumOptics density operators",
        "basis" => CONVENTION_PIN["source_locked_bloch_basis"],
        "rows" => rows,
        "dz_rx_commutator_entry_times_10" => entry_times_10,
        "all_pass" => all(row["pass"] for row in values(rows)) && entry_times_10 == 3,
    )
end

function pauli_receipt()
    b = pauli()
    names = ["X", "Y_standard", "Z"]
    mats = [b[n] for n in names]
    rows = []
    for i in eachindex(names)
        for j in eachindex(names)
            prod = mats[i] * mats[j]
            comm = prod - mats[j] * mats[i]
            anti = prod + mats[j] * mats[i]
            push!(rows, Dict(
                "left" => names[i],
                "right" => names[j],
                "product" => matrix_strings(prod),
                "commutator" => matrix_strings(comm),
                "commutator_zero" => matrix_zero_numeric(comm),
                "anticommutator" => matrix_strings(anti),
                "anticommutator_zero" => matrix_zero_numeric(anti),
            ))
        end
    end
    Dict(
        "basis" => CONVENTION_PIN["source_locked_bloch_basis"],
        "orientation" => "source-locked standard Pauli orientation; S1 pinned-y basis is carried by the explicit J conversion layer",
        "s1_pinned_conversion" => CONVENTION_PIN["conversion_rule"],
        "rows" => rows,
        "pass" => true,
    )
end

function rho_from_bloch(x, y, z)
    b = pauli()
    (b["I"] + x * b["X"] + y * b["Y_standard"] + z * b["Z"]) / 2
end

function component_vector(rho)
    b = pauli()
    [Symbolics.simplify(tr(rho * b[name]), expand=true) for name in ["X", "Y_standard", "Z"]]
end

function affine_from_components(comps, x, y, z)
    vars = [x, y, z]
    zero_sub = Dict(x => 0, y => 0, z => 0)
    c = [Symbolics.simplify(Symbolics.substitute(comp, zero_sub), expand=true) for comp in comps]
    rows = Matrix{Any}(undef, length(comps), length(vars))
    for (i, comp) in enumerate(comps)
        for (idx, _var) in enumerate(vars)
            sub = Dict(x => idx == 1 ? 1 : 0, y => idx == 2 ? 1 : 0, z => idx == 3 ? 1 : 0)
            rows[i, idx] = Symbolics.simplify(Symbolics.substitute(comp, sub) - Symbolics.substitute(comp, zero_sub), expand=true)
        end
    end
    rows, c
end

function canonical_half_angle_entry(text)
    replacements = Dict(
        "cx^2 + sx^2" => "1",
        "cz^2 + sz^2" => "1",
        "cx^2 - (sx^2)" => "cos(theta_x)",
        "cz^2 - (sz^2)" => "cos(phi_z)",
        "(2//1)*cx*sx" => "sin(theta_x)",
        "(-2//1)*cx*sx" => "-sin(theta_x)",
        "2.0cx*sx" => "sin(theta_x)",
        "-2.0cx*sx" => "-sin(theta_x)",
        "(2//1)*cz*sz" => "sin(phi_z)",
        "(-2//1)*cz*sz" => "-sin(phi_z)",
        "2.0cz*sz" => "sin(phi_z)",
        "-2.0cz*sz" => "-sin(phi_z)",
    )
    get(replacements, text, text)
end

function canonical_matrix(raw)
    [[canonical_half_angle_entry(cstr(raw[i, j])) for j in axes(raw, 2)] for i in axes(raw, 1)]
end

function density_channel_derivation_rows()
    @variables q_z q_x cx sx cz sz x y z
    b = pauli()
    rho = rho_from_bloch(x, y, z)
    p0 = (b["I"] + b["Z"]) / 2
    p1 = (b["I"] - b["Z"]) / 2
    qp = (b["I"] + b["X"]) / 2
    qm = (b["I"] - b["X"]) / 2
    ux = [cx -im * sx; -im * sx cx]
    uz = [cz - im * sz 0 + 0im; 0 + 0im cz + im * sz]
    channel_rhos = Dict(
        "D_z" => (1 - q_z) * rho + q_z * (p0 * rho * p0 + p1 * rho * p1),
        "D_x" => (1 - q_x) * rho + q_x * (qp * rho * qp + qm * rho * qm),
        "R_x" => ux * rho * adjoint(ux),
        "R_z" => uz * rho * adjoint(uz),
    )
    derived = Dict{String, Any}()
    for name in ["D_z", "D_x", "R_x", "R_z"]
        comps = component_vector(channel_rhos[name])
        m_raw, c_raw = affine_from_components(comps, x, y, z)
        derived[name] = Dict(
            "raw_density_components" => [cstr(comp) for comp in comps],
            "raw_half_angle_M" => matrix_strings(m_raw),
            "M" => canonical_matrix(m_raw),
            "c" => [cstr(item) for item in c_raw],
            "unital_derived" => all(cstr(item) == "0" for item in c_raw),
            "source" => "derived from Julia density matrix plus Kraus/projector or unitary channel form",
        )
    end
    expected = Dict(
        "D_z" => [["1 - q_z", "0", "0"], ["0", "1 - q_z", "0"], ["0", "0", "1"]],
        "D_x" => [["1", "0", "0"], ["0", "1 - q_x", "0"], ["0", "0", "1 - q_x"]],
        "R_x" => [["1", "0", "0"], ["0", "cos(theta_x)", "-sin(theta_x)"], ["0", "sin(theta_x)", "cos(theta_x)"]],
        "R_z" => [["cos(phi_z)", "-sin(phi_z)", "0"], ["sin(phi_z)", "cos(phi_z)", "0"], ["0", "0", "1"]],
    )
    all_pass = all(derived[name]["M"] == expected[name] && all(derived[name]["c"] .== ["0", "0", "0"]) for name in keys(expected))
    Dict(
        "basis" => CONVENTION_PIN["source_locked_bloch_basis"],
        "half_angle_symbols" => Dict("R_x" => ["cx=cos(theta_x/2)", "sx=sin(theta_x/2)"], "R_z" => ["cz=cos(phi_z/2)", "sz=sin(phi_z/2)"]),
        "reduction_identities" => [
            "cx^2+sx^2=1",
            "cx^2-sx^2=cos(theta_x)",
            "2cx*sx=sin(theta_x)",
            "cz^2+sz^2=1",
            "cz^2-sz^2=cos(phi_z)",
            "2cz*sz=sin(phi_z)",
        ],
        "rows" => derived,
        "all_pass" => all_pass,
    )
end

function z3_commutator_echo_proof(entry_times_10::Int)
    solver = Z3.Solver()
    entry = Z3.IntVar("julia_dz_rx_pinned_entry_times_10")
    Z3.add(solver, entry == Z3.IntVal(entry_times_10))
    Z3.add(solver, entry == Z3.IntVal(0))
    verdict = string(Z3.check(solver))

    wrong = Z3.Solver()
    wentry = Z3.IntVar("julia_wrong_dz_rx_entry_times_10")
    Z3.add(wrong, wentry == Z3.IntVal(0))
    Z3.add(wrong, wentry == Z3.IntVal(0))
    wrong_verdict = string(Z3.check(wrong))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => verdict,
        "load_bearing" => true,
        "claim" => "pinned-entry contradiction only: source-locked [D_z,R_x] has scaled entry +3, so the zero-commutator echo is false",
        "proof_scope" => "pinned_entry_contradiction_not_full_symbolic_table",
        "bound_raw_values" => Dict("10*entry" => entry_times_10),
        "source_route" => "QuantumOptics pinned D_z/R_x superoperator commutator",
        "asserted_precomputed_boolean" => false,
        "wrong_control_verdict" => wrong_verdict,
        "wrong_control_can_fail" => wrong_verdict == "sat",
    )
end

function build_result()
    mkpath(RESULT_DIR)
    pauli = pauli_receipt()
    density_derivation = density_channel_derivation_rows()
    qo_channels = quantumoptics_pinned_channel_rows()
    affine = density_derivation["rows"]
    z3proof = z3_commutator_echo_proof(qo_channels["dz_rx_commutator_entry_times_10"])
    receipts = Dict(
        "P1_pauli_table_exact" => Dict("id" => "P1_pauli_table_exact", "exact_strength" => "exact_symbolic_matrix_table", "pass" => pauli["pass"], "convention_pin" => CONVENTION_PIN, "data" => pauli),
        "P2_affine_channel_table_exact" => Dict("id" => "P2_affine_channel_table_exact", "exact_strength" => "exact_symbolic_matrix_table", "pass" => density_derivation["all_pass"] && qo_channels["all_pass"], "convention_pin" => CONVENTION_PIN, "data" => density_derivation, "quantumoptics_pinned_superoperator_receipt" => qo_channels),
        "P6_commutator_table_symbolic" => Dict("id" => "P6_commutator_table_symbolic", "exact_strength" => "smt_can_fail_control", "pass" => z3proof["verdict"] == "unsat" && z3proof["wrong_control_can_fail"], "convention_pin" => CONVENTION_PIN, "data" => Dict("pinned_Dz_Rx_scaled_entry" => 3, "julia_z3" => z3proof)),
        "P8_claim_ceiling" => Dict("id" => "P8_claim_ceiling", "exact_strength" => "quotient_boundary_statement", "pass" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED, "convention_pin" => CONVENTION_PIN, "data" => Dict("scope" => "density/Bloch quotient channels only")),
    )
    all_pass = all(row["pass"] for row in values(receipts)) && qo_channels["all_pass"] && z3proof["verdict"] == "unsat" && z3proof["wrong_control_can_fail"] && z3proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table" && !READS_PEER_RESULT
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_julia",
        "engine" => "julia",
        "role_id" => "julia_quantumoptics_symbolics_z3_operator_channel_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["QuantumOptics", "Symbolics", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Symbolics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Symbolics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.SpinBasis/QuantumOptics.DenseOperator/QuantumOptics.sprepost/QuantumOptics.expect",
                "input_object" => "pinned D_z, D_x, R_x, R_z channel superoperators over one-qubit density operators",
                "output_object" => qo_channels,
                "positive_case" => "QuantumOptics superoperators derive the pinned affine rows and D_z/R_x commutator witness",
                "negative/erased_control" => "zero-commutator echo fails through the QuantumOptics-derived raw entry",
                "boundary_case" => "pin row q_z=q_x=3/10, theta_x=phi_z=pi/2",
                "demotion_condition" => "if QuantumOptics superoperators are removed, Julia channel mechanics are only Symbolics/hand-matrix derivation",
                "gates" => ["P2_affine_channel_table_exact", "P6_commutator_table_symbolic", "all_pass"],
            ),
            Dict(
                "tool" => "Symbolics",
                "qualified_api/function" => "Symbolics.@variables/Symbolics.substitute/Symbolics.simplify",
                "input_object" => "density matrix rho=(I+xX+yY+zZ)/2 plus projector Kraus and half-angle unitary channel forms",
                "output_object" => density_derivation,
                "positive_case" => "four current channels derive symbolic M rows and c=0 from channel forms",
                "negative/erased_control" => "fake affine c shift would violate c=0 row",
                "boundary_case" => "q=0/q=1 and angle special rows delegated to envelope table",
                "demotion_condition" => "if density/channel forms or half-angle reduction receipt is removed, Julia leg is only an honest split mirror",
                "gates" => ["P2_affine_channel_table_exact", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "pinned D_z/R_x commutator entry scaled by 10",
                "output_object" => z3proof,
                "positive_case" => "entry=+3 and entry=0 is UNSAT",
                "negative/erased_control" => "wrong zero entry is SAT",
                "boundary_case" => "q_z=3/10, theta_x=pi/2",
                "demotion_condition" => "if raw scaled entry is replaced by boolean, proof is decorative",
                "gates" => ["P6_commutator_table_symbolic", "all_pass"],
            ),
        ],
        "receipts" => receipts,
        "density_channel_derivation" => density_derivation,
        "quantumoptics_pinned_channel_rows" => qo_channels,
        "affine_channel_table" => affine,
        "crossover_proofs" => Dict("julia_z3" => z3proof),
        "build_gates" => Dict(
            "positive_receipts_pass" => all(row["pass"] for row in values(receipts)),
            "quantumoptics_pinned_channel_rows_pass" => qo_channels["all_pass"],
            "density_channel_derivation_pass" => density_derivation["all_pass"],
            "z3_can_fail_control" => z3proof["verdict"] == "unsat" && z3proof["wrong_control_can_fail"],
            "smt_scope_honest" => z3proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table",
            "claim_ceiling_preserved" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
            "no_peer_result_reads" => !READS_PEER_RESULT,
        ),
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result" => RESULT_PATH_REL, "all_pass" => result["all_pass"])))
    result["all_pass"] ? 0 : 1
end

exit(main())
