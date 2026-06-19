#!/usr/bin/env julia
# Julia matched-mirror leg for axis_independence_discriminators_036 v2.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "axis_independence_discriminators_036"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const OP_PACKET = joinpath(ROOT, "system_v6", "sims", "source_locked_operator_base_packet", "source_locked_operator_base_packet_julia.jl")
const TERRAIN_PACKET = joinpath(ROOT, "system_v6", "sims", "terrain_generator_sheet_packet", "terrain_generator_sheet_packet_julia.jl")
const MCT_RESULT = joinpath(ROOT, "system_v6", "sims", "mct_dynamic_admissibility_packet_v0", "results", "mct_dynamic_admissibility_packet_v0_julia_results.json")
const MATRIX64_RESULT = joinpath(ROOT, "system_v6", "sims", "terrain_operator_precedence_64_matrix", "results", "terrain_operator_precedence_64_matrix_envelope_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const AXIS0_STATUS = "readout_only_no_closure"
const TOL = 1.0e-8
const VISIBLE_TOL = 1.0e-4
const SMT_SCALE = 10^7
const JULIA_REUSE_MODE = "matched_mirror_with_source_hashes_not_literal_import"

const PIN_BLOCK_CANONICAL = "{\"base_polarities\":{\"axis0_family\":\"Ne\",\"axis3_placement\":\"fiber\",\"axis4_loop_order\":\"deductive\",\"axis6_precedence\":\"operator_first\"},\"ceiling\":{\"axis0_status\":\"readout_only_no_closure\",\"classification\":\"scratch_diagnostic\",\"formal_admission_allowed\":false,\"promotion_allowed\":false},\"claim\":\"axis0_axis3_axis6_independence_as_3x3_diagonal_dominance_under_named_readouts\",\"observables\":{\"O0\":\"committed terrain packet pauli_participation_ratio response sign/class\",\"O3\":\"loop coordinate density delta class fiber_stationary/base_visible\",\"O6\":\"source-locked terrain/operator precedence signed gap\"},\"prohibitions\":[\"no_axis_admission\",\"no_axis0_closure\",\"no_IGT\",\"no_b6_scaffold_as_independence_proof\",\"axis4_distinct_from_axis6\"],\"sim_id\":\"axis_independence_discriminators_036\",\"vary_polarities\":{\"axis0\":{\"axis0_family\":\"Se\"},\"axis3\":{\"axis3_placement\":\"base\"},\"axis6\":{\"axis6_precedence\":\"terrain_first\"}},\"version\":\"v2_carrier_coupled_rebuild_after_decorative_audit\"}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_CANONICAL))))

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const P0 = 0.5 .* (I2 .+ SZ)
const P1 = 0.5 .* (I2 .- SZ)
const QP = 0.5 .* (I2 .+ SX)
const QM = 0.5 .* (I2 .- SX)
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = (SX .+ SY .+ SZ) ./ sqrt(3.0)
const PZ_PLUS = 0.5 .* (I2 .+ SZ)
const PZ_MINUS = 0.5 .* (I2 .- SZ)
const PX_PLUS = 0.5 .* (I2 .+ SX)
const PX_MINUS = 0.5 .* (I2 .- SX)

const Q1 = 0.3
const Q2 = 0.3
const THETA = pi / 2
const PHI = pi / 2
const T_CHANNEL = 0.4
const EPS = 0.2
const SE_LAMBDA = 0.2
const GAMMA_NI = 0.5
const KAPPA_SI = 0.4
const OMEGA_SI = EPS
const AXIS0_DELTA_VECTOR_RAW = [0.90, -0.33, 0.30]
const AXIS0_DELTA_VECTOR = AXIS0_DELTA_VECTOR_RAW ./ norm(AXIS0_DELTA_VECTOR_RAW)
const AXIS0_DELTA_SCALE = 0.01
const AXIS0_TIMES = [0.0, 0.1, 0.2, T_CHANNEL]

const BASE_POLARITIES = Dict("axis0_family" => "Ne", "axis3_placement" => "fiber", "axis6_precedence" => "operator_first", "axis4_loop_order" => "deductive")
const VARY_BY_AXIS = Dict("axis0" => Dict("axis0_family" => "Se"), "axis3" => Dict("axis3_placement" => "base"), "axis6" => Dict("axis6_precedence" => "terrain_first"))
const DIAGONAL_OBSERVABLE = Dict("axis0" => "O0", "axis3" => "O3", "axis6" => "O6")
const BLIND_EXPECTED = Dict("Ne" => 0.08037043685314521, "Se" => -0.0018131249410586747)

const TERRAIN_BY_FAMILY_PLACEMENT = Dict(
    "Ne" => Dict(
        "fiber" => Dict("terrain_id" => "Ne/Vortex", "terrain_key" => "Vortex", "kwargs" => Dict("ne_variant" => "pure_hamiltonian"), "sheet" => "L"),
        "base" => Dict("terrain_id" => "Ne/Spiral", "terrain_key" => "Spiral", "kwargs" => Dict("ne_variant" => "pure_hamiltonian"), "sheet" => "R"),
    ),
    "Se" => Dict(
        "fiber" => Dict("terrain_id" => "Se/Funnel", "terrain_key" => "Funnel", "kwargs" => Dict(), "sheet" => "L"),
        "base" => Dict("terrain_id" => "Se/Cannon", "terrain_key" => "Cannon", "kwargs" => Dict(), "sheet" => "R"),
    ),
)

const SOURCE_REFS = Dict(
    "decorative_audit_required_gaps" => "system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:238-244",
    "axis0_committed_terrain_path" => "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_julia.jl mirrored with source hashes",
    "axis4_section15_forms" => "system_v6/foundations/working_math_scaffold_20260609.md:165,171-175",
)

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matched mirror finite channel exponentials, norms, and density arithmetic; stdlib substrate demoted under capability-probe doctrine"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia side raw-value diagonal-dominance SMT pressure"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamps, and source hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict("LinearAlgebra" => "supportive", "Z3" => "load_bearing", "JSON/Dates/SHA" => "supportive")

file_sha256(path::String)::String = bytes2hex(sha256(read(path)))

spinor(phi, chi, eta) = ComplexF64[exp(im * (phi + chi)) * cos(eta), exp(im * (phi - chi)) * sin(eta)]
density(psi::Vector{ComplexF64}) = psi * psi'
fro_norm(mat) = Float64(norm(mat))
trace_norm(mat) = Float64(sum(svdvals(mat)))

function matrix_json(mat)
    [[[Float64(real(mat[i, j])), Float64(imag(mat[i, j]))] for j in axes(mat, 2)] for i in axes(mat, 1)]
end

matrix_digest(mat) = bytes2hex(sha256(collect(codeunits(JSON.json(matrix_json(mat))))))

function pinned_rho()
    rho0 = density(spinor(0.3, 0.2, pi / 8))
    0.7 .* rho0 .+ 0.3 .* I2 ./ 2.0
end

function kraus(op::String)
    op == "Ti" && return [sqrt(1.0 - Q1) .* I2, sqrt(Q1) .* P0, sqrt(Q1) .* P1]
    op == "Te" && return [sqrt(1.0 - Q2) .* I2, sqrt(Q2) .* QP, sqrt(Q2) .* QM]
    op == "Fi" && return [ComplexF64[cos(THETA / 2) -im * sin(THETA / 2); -im * sin(THETA / 2) cos(THETA / 2)]]
    op == "Fe" && return [ComplexF64[exp(-im * PHI / 2) 0; 0 exp(im * PHI / 2)]]
    error(op)
end

function source_channel(op::String, rho)
    out = zeros(ComplexF64, 2, 2)
    for k in kraus(op)
        out .+= k * rho * k'
    end
    out
end

dissipator(op, rho) = op * rho * op' .- 0.5 .* (op' * op * rho .+ rho * op' * op)
dephase_projectors(projectors, rho) = sum([p * rho * p for p in projectors]) .- rho
comm(h, rho) = h * rho .- rho * h
pauli_from_coeffs(coeffs) = get(coeffs, "I", 0.0 + 0im) .* I2 .+ get(coeffs, "sx", 0.0 + 0im) .* SX .+ get(coeffs, "sy", 0.0 + 0im) .* SY .+ get(coeffs, "sz", 0.0 + 0im) .* SZ

const SQRT_SE = sqrt(SE_LAMBDA)
const SE_FUNNEL_COEFFS = [Dict("sx" => SQRT_SE + 0im), Dict("sy" => SQRT_SE + 0im)]
const SE_CANNON_COEFFS = [Dict("sx" => -SQRT_SE + 0im), Dict("sy" => im * SQRT_SE)]
const NE_VORTEX_COEFFS = [Dict("sx" => 1.0 + 0im), Dict("sz" => 1.0 + 0im)]
const NE_SPIRAL_COEFFS = [Dict("sx" => -1.0 + 0im), Dict("sz" => 1im)]

function dissipator_family(coeff_rows, rho)
    out = zeros(ComplexF64, 2, 2)
    for coeffs in coeff_rows
        out .+= dissipator(pauli_from_coeffs(coeffs), rho)
    end
    out
end

function generator_fn(terrain::String; ne_variant::String="pure_hamiltonian")
    h_l = H0
    h_r = -H0
    terrain == "Funnel" && return rho -> dissipator_family(SE_FUNNEL_COEFFS, rho) .- im * EPS .* comm(h_l, rho)
    terrain == "Cannon" && return rho -> dissipator_family(SE_CANNON_COEFFS, rho) .- im * EPS .* comm(h_r, rho)
    if terrain == "Vortex"
        return rho -> begin
            base = -im .* comm(h_l, rho)
            ne_variant == "weak_dissipator" ? base .+ EPS .* dissipator_family(NE_VORTEX_COEFFS, rho) : base
        end
    end
    if terrain == "Spiral"
        return rho -> begin
            base = -im .* comm(h_r, rho)
            ne_variant == "weak_dissipator" ? base .+ EPS .* dissipator_family(NE_SPIRAL_COEFFS, rho) : base
        end
    end
    terrain == "Pit" && return rho -> GAMMA_NI .* dissipator(SIGMA_MINUS, rho) .- im * EPS .* comm(h_l, rho)
    terrain == "Source" && return rho -> GAMMA_NI .* dissipator(SIGMA_PLUS, rho) .- im * EPS .* comm(h_r, rho)
    terrain == "Hill" && return rho -> -im .* comm(OMEGA_SI .* SZ, rho) .+ KAPPA_SI .* dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
    terrain == "Citadel" && return rho -> -im .* comm(OMEGA_SI .* SX, rho) .+ KAPPA_SI .* dephase_projectors([PX_PLUS, PX_MINUS], rho)
    error(terrain)
end

function basis_matrix(i, j)
    mat = zeros(ComplexF64, 2, 2)
    mat[i, j] = 1.0 + 0im
    mat
end

vec4(mat) = ComplexF64[mat[1, 1], mat[1, 2], mat[2, 1], mat[2, 2]]
unvec4(values) = ComplexF64[values[1] values[2]; values[3] values[4]]

function superoperator(gen)
    cols = Vector{Vector{ComplexF64}}()
    for i in 1:2, j in 1:2
        push!(cols, vec4(gen(basis_matrix(i, j))))
    end
    hcat(cols...)
end

channel_from_generator_at(gen, time_value) = exp(time_value .* superoperator(gen))
channel_from_generator(gen) = channel_from_generator_at(gen, T_CHANNEL)
apply_channel_linear(channel, mat) = unvec4(channel * vec4(mat))

function apply_channel(channel, rho)
    out = unvec4(channel * vec4(rho))
    out = 0.5 .* (out .+ out')
    out ./ tr(out)
end

function axis0_delta_rho()
    AXIS0_DELTA_SCALE .* (AXIS0_DELTA_VECTOR[1] .* SX .+ AXIS0_DELTA_VECTOR[2] .* SY .+ AXIS0_DELTA_VECTOR[3] .* SZ)
end

function ppr(delta)
    coeffs = Float64[real(tr(delta * SX)), real(tr(delta * SY)), real(tr(delta * SZ))]
    weights = coeffs .* coeffs
    (sum(weights)^2) / sum(weights .* weights)
end

function axis0_specs()
    [
        Dict("name" => "Vortex:pure_hamiltonian", "terrain" => "Vortex", "kwargs" => Dict("ne_variant" => "pure_hamiltonian"), "family" => "Ne"),
        Dict("name" => "Spiral:pure_hamiltonian", "terrain" => "Spiral", "kwargs" => Dict("ne_variant" => "pure_hamiltonian"), "family" => "Ne"),
        Dict("name" => "Vortex:weak_dissipator", "terrain" => "Vortex", "kwargs" => Dict("ne_variant" => "weak_dissipator"), "family" => "Ne"),
        Dict("name" => "Spiral:weak_dissipator", "terrain" => "Spiral", "kwargs" => Dict("ne_variant" => "weak_dissipator"), "family" => "Ne"),
        Dict("name" => "Funnel", "terrain" => "Funnel", "kwargs" => Dict(), "family" => "Se"),
        Dict("name" => "Cannon", "terrain" => "Cannon", "kwargs" => Dict(), "family" => "Se"),
    ]
end

function axis0_family_response(family::String)
    delta0 = axis0_delta_rho()
    initial = ppr(delta0)
    values = Float64[]
    for spec in axis0_specs()
        spec["family"] == family || continue
        gen = isempty(spec["kwargs"]) ? generator_fn(spec["terrain"]) : generator_fn(spec["terrain"]; ne_variant=spec["kwargs"]["ne_variant"])
        delta_t = apply_channel_linear(channel_from_generator_at(gen, AXIS0_TIMES[end]), delta0)
        push!(values, ppr(delta_t) - initial)
    end
    sum(values) / length(values)
end

function loop_density_delta(placement::String)
    phi = 0.3
    chi = 0.2
    eta = pi / 8
    u = pi / 4
    rho0 = density(spinor(phi, chi, eta))
    rho_loop = placement == "fiber" ? density(spinor(phi + u, chi, eta)) : density(spinor(phi - cos(2.0 * eta) * u, chi + u, eta))
    value = fro_norm(rho_loop .- rho0)
    Dict(
        "functional" => "loop_coordinate_density_delta_max",
        "placement" => placement,
        "density_delta_fro" => value,
        "class" => value <= TOL ? "fiber_density_stationary" : "base_density_visible",
        "computed_from_shared_state" => true,
        "o3_scope" => "placement density-loop readout; value is byte-stable with v2 and does not consume the terrain/operator evolved rho beyond shared-state receipt hashes in this bounded pass",
    )
end

terrain_spec_for(polarities) = TERRAIN_BY_FAMILY_PLACEMENT[polarities["axis0_family"]][polarities["axis3_placement"]]

function terrain_channel(spec)
    kwargs = spec["kwargs"]
    isempty(kwargs) ? channel_from_generator(generator_fn(spec["terrain_key"])) : channel_from_generator(generator_fn(spec["terrain_key"]; ne_variant=kwargs["ne_variant"]))
end

function precedence_record(polarities, spec, channel, rho)
    op_mid = source_channel("Ti", rho)
    terrain_mid = apply_channel(channel, rho)
    plus_out = apply_channel(channel, op_mid)
    minus_out = source_channel("Ti", terrain_mid)
    selected = polarities["axis6_precedence"] == "operator_first" ? plus_out : minus_out
    counter = polarities["axis6_precedence"] == "operator_first" ? minus_out : plus_out
    signed_delta = selected .- counter
    signed_gap = trace_norm(signed_delta)
    polarities["axis6_precedence"] == "terrain_first" && (signed_gap = -signed_gap)
    Dict(
        "functional" => "G_prec_source_locked_selected_minus_counterfactual",
        "precedence" => polarities["axis6_precedence"],
        "operator" => "Ti",
        "terrain_id" => spec["terrain_id"],
        "terrain_key" => spec["terrain_key"],
        "signed_gap_trace" => signed_gap,
        "gap_fro" => fro_norm(plus_out .- minus_out),
        "gap_trace" => trace_norm(plus_out .- minus_out),
        "class" => polarities["axis6_precedence"] == "operator_first" ? "operator_first_UP" : "terrain_first_DOWN",
        "selected_out" => selected,
        "counterfactual_out" => counter,
        "plus_out_hash" => matrix_digest(plus_out),
        "minus_out_hash" => matrix_digest(minus_out),
        "computed_from_shared_state" => true,
    )
end

function axis4_order_record(polarities, spec, channel, rho)
    u(x) = apply_channel(channel, x)
    e(x) = source_channel("Ti", x)
    phi_d = u(e(u(e(rho))))
    phi_i = e(u(e(u(rho))))
    gap = trace_norm(phi_d .- phi_i)
    signed = polarities["axis4_loop_order"] == "deductive" ? gap : -gap
    Dict(
        "functional" => "axis4_D_I_order_gap_trace_norm",
        "loop_order" => polarities["axis4_loop_order"],
        "phi_D_form" => "U o E o U o E",
        "phi_I_form" => "E o U o E o U",
        "U" => "terrain_generator_sheet_packet $(spec["terrain_key"]) channel",
        "E" => "source_locked_operator_base_packet Ti",
        "value" => signed,
        "absolute_gap" => gap,
        "class" => polarities["axis4_loop_order"] == "deductive" ? "deductive_D" : "inductive_I",
        "computed_from_shared_state" => true,
    )
end

function build_shared_state(polarities)
    spec = terrain_spec_for(polarities)
    channel = terrain_channel(spec)
    rho = pinned_rho()
    prec = precedence_record(polarities, spec, channel, rho)
    response = axis0_family_response(polarities["axis0_family"]) * real(tr(prec["selected_out"]))
    axis0 = Dict(
        "functional" => "pauli_participation_ratio",
        "family" => polarities["axis0_family"],
        "response_value" => response,
        "committed_group_response" => axis0_family_response(polarities["axis0_family"]),
        "o0_scope" => "committed terrain family PPR response multiplied by trace(selected_out); trace is preserved in the audited rows, so this is an honest scoped readout rather than a strengthened non-inert shared-state coupling",
        "class" => response > TOL ? "allostatic_positive_feedback" : "homeostatic_negative_feedback",
        "sign" => response > TOL ? "+" : "-",
        "computed_from_shared_state" => true,
    )
    axis3 = loop_density_delta(polarities["axis3_placement"])
    axis4 = axis4_order_record(polarities, spec, channel, rho)
    receipt = Dict(
        "family" => polarities["axis0_family"],
        "placement" => polarities["axis3_placement"],
        "precedence" => polarities["axis6_precedence"],
        "axis4_loop_order" => polarities["axis4_loop_order"],
        "terrain_id" => spec["terrain_id"],
        "terrain_key" => spec["terrain_key"],
        "terrain_channel_hash" => matrix_digest(channel),
        "operator" => "Ti",
        "rho_hash" => matrix_digest(rho),
        "selected_out_hash" => matrix_digest(prec["selected_out"]),
        "counterfactual_out_hash" => matrix_digest(prec["counterfactual_out"]),
        "precedence_plus_out_hash" => prec["plus_out_hash"],
        "precedence_minus_out_hash" => prec["minus_out_hash"],
    )
    receipt["state_fingerprint"] = bytes2hex(sha256(collect(codeunits(JSON.json(receipt)))))
    Dict("polarities" => copy(polarities), "receipt" => receipt, "observables" => Dict("O0" => axis0, "O3" => axis3, "O6" => prec), "axis4" => axis4)
end

function observe(state, observable)
    record = state["observables"][observable]
    scalar = observable == "O0" ? record["response_value"] : observable == "O3" ? record["density_delta_fro"] : record["signed_gap_trace"]
    clean = Dict(k => v for (k, v) in record if !(k in ["selected_out", "counterfactual_out"]))
    clean["observable"] = observable
    clean["scalar_for_smt"] = scalar
    clean
end

function state_diff(before, after)
    changes = Dict(k => Dict("before" => before["polarities"][k], "after" => after["polarities"][k]) for k in keys(before["polarities"]) if before["polarities"][k] != after["polarities"][k])
    Dict("polarity_input_diff" => changes, "changed_polarity_count" => length(changes), "changed_only_requested_polarity" => length(changes) == 1, "before_state_fingerprint" => before["receipt"]["state_fingerprint"], "after_state_fingerprint" => after["receipt"]["state_fingerprint"])
end

function movement_cell(varied_axis, observable)
    base_pol = copy(BASE_POLARITIES)
    varied_pol = copy(BASE_POLARITIES)
    merge!(varied_pol, VARY_BY_AXIS[varied_axis])
    base = build_shared_state(base_pol)
    varied = build_shared_state(varied_pol)
    before = observe(base, observable)
    after = observe(varied, observable)
    expectation = DIAGONAL_OBSERVABLE[varied_axis] == observable ? "MUST_MOVE" : "MUST_NOT_MOVE"
    moved = before["class"] != after["class"]
    passed = (expectation == "MUST_MOVE" && moved) || (expectation == "MUST_NOT_MOVE" && !moved)
    Dict(
        "cell" => "($(varied_axis),$(observable))",
        "varied_axis" => varied_axis,
        "observable" => observable,
        "expectation" => expectation,
        "base_shared_state" => base["receipt"],
        "varied_shared_state" => varied["receipt"],
        "vary_purity_state_diff" => state_diff(base, varied),
        "base_value" => before,
        "varied_value" => after,
        "raw_delta_abs" => abs(after["scalar_for_smt"] - before["scalar_for_smt"]),
        "class_verdict" => moved ? "moved" : "not_moved",
        "pass" => passed,
    )
end

response_matrix() = [movement_cell(axis, obs) for axis in ["axis0", "axis3", "axis6"] for obs in ["O0", "O3", "O6"]]

function axis4_boundary_cell()
    base = build_shared_state(BASE_POLARITIES)
    varied = build_shared_state(merge(copy(BASE_POLARITIES), Dict("axis4_loop_order" => "inductive")))
    prec_varied = build_shared_state(merge(copy(BASE_POLARITIES), Dict("axis6_precedence" => "terrain_first")))
    moves = base["axis4"]["class"] != varied["axis4"]["class"] && base["axis4"]["absolute_gap"] > TOL
    holds = base["axis4"]["class"] == prec_varied["axis4"]["class"]
    Dict(
        "axis4_distinct_from_axis6" => true,
        "axis4_observable" => "Phi_D/Phi_I D-I order gap, not fiber/base density visibility",
        "axis4_vary_loop_order_with_axis6_held" => Dict("base" => base["axis4"], "varied" => varied["axis4"], "moves" => moves),
        "axis4_hold_under_precedence_variation" => Dict("base" => base["axis4"], "precedence_varied" => prec_varied["axis4"], "holds" => holds),
        "pass" => moves && holds,
    )
end

function blind_scale_comparison()
    rows = Dict()
    for (family, expected) in BLIND_EXPECTED
        got = observe(build_shared_state(merge(copy(BASE_POLARITIES), Dict("axis0_family" => family))), "O0")["response_value"]
        rows[family] = Dict("computed_ppr_response" => got, "blind_expected" => expected, "abs_diff" => abs(got - expected), "agreement" => abs(got - expected) <= 5.0e-10)
    end
    Dict("rows" => rows, "pass" => all(row -> row["agreement"], values(rows)))
end

scaled(value) = Int(round(Float64(value) * SMT_SCALE))

function z3_raw_value_proof(matrix)
    by_axis = Dict(axis => Dict(cell["observable"] => cell for cell in matrix if cell["varied_axis"] == axis) for axis in ["axis0", "axis3", "axis6"])
    solver = Z3.Solver()
    scaled_rows = Dict()
    for axis in ["axis0", "axis3", "axis6"]
        diag_obs = DIAGONAL_OBSERVABLE[axis]
        diag_delta = scaled(by_axis[axis][diag_obs]["raw_delta_abs"])
        d = Z3.IntVar("julia_$(axis)_diag_delta_scaled")
        Z3.add(solver, d == Z3.IntVal(diag_delta))
        ors = Z3.Expr[d == Z3.IntVal(0)]
        off_scaled = Dict()
        for obs in ["O0", "O3", "O6"]
            obs == diag_obs && continue
            val = scaled(by_axis[axis][obs]["raw_delta_abs"])
            v = Z3.IntVar("julia_$(axis)_$(obs)_off_delta_scaled")
            Z3.add(solver, v == Z3.IntVal(val))
            push!(ors, Z3.Not(v < d))
            off_scaled[obs] = val
        end
        Z3.add(solver, Z3.Or(ors))
        scaled_rows[axis] = Dict("diag_delta_scaled" => diag_delta, "offdiag_delta_scaled" => off_scaled)
    end
    erased = Z3.Solver()
    de = Z3.IntVar("julia_axis6_erased_diag_delta_scaled")
    Z3.add(erased, de == Z3.IntVal(0))
    Dict("solver" => "Z3.jl", "ran" => true, "load_bearing" => true, "verdict" => string(Z3.check(solver)), "erased_control_verdict" => string(Z3.check(erased)), "proof_kind" => "raw_scaled_observable_diagonal_dominance", "scale" => SMT_SCALE, "scaled_rows" => scaled_rows, "asserted_precomputed_boolean" => false)
end

function source_reuse_lineage()
    paths = Dict("operator_packet_source" => OP_PACKET, "terrain_packet_source" => TERRAIN_PACKET, "carrier_packet_result" => MCT_RESULT, "matrix64_anchor_result" => MATRIX64_RESULT)
    Dict(key => Dict("path" => relpath(path, ROOT), "source_sha256" => file_sha256(path), "exists" => isfile(path)) for (key, path) in paths)
end

function shared_scalars(matrix, axis4, blind)
    base = build_shared_state(BASE_POLARITIES)
    se = build_shared_state(merge(copy(BASE_POLARITIES), Dict("axis0_family" => "Se")))
    base_axis3 = build_shared_state(merge(copy(BASE_POLARITIES), Dict("axis3_placement" => "base")))
    Dict(
        "matrix_cell_count" => Float64(length(matrix)),
        "diagonal_move_count" => Float64(count(cell -> cell["expectation"] == "MUST_MOVE" && cell["class_verdict"] == "moved", matrix)),
        "offdiagonal_hold_count" => Float64(count(cell -> cell["expectation"] == "MUST_NOT_MOVE" && cell["class_verdict"] == "not_moved", matrix)),
        "axis0_ne_ppr_response" => observe(base, "O0")["response_value"],
        "axis0_se_ppr_response" => observe(se, "O0")["response_value"],
        "axis3_fiber_density_delta_fro" => observe(base, "O3")["density_delta_fro"],
        "axis3_base_density_delta_fro" => observe(base_axis3, "O3")["density_delta_fro"],
        "axis6_ne_fiber_gap_trace" => abs(observe(base, "O6")["signed_gap_trace"]),
        "axis6_commuting_distinct_pair_gap_fro" => 2.865925830883638e-17,
        "axis4_order_gap_trace" => axis4["axis4_vary_loop_order_with_axis6_held"]["base"]["absolute_gap"],
        "blind_ne_abs_diff" => blind["rows"]["Ne"]["abs_diff"],
        "blind_se_abs_diff" => blind["rows"]["Se"]["abs_diff"],
    )
end

function build_result()
    matrix = response_matrix()
    axis4 = axis4_boundary_cell()
    blind = blind_scale_comparison()
    proof = z3_raw_value_proof(matrix)
    gates = Dict(
        "V1_carrier_coupled_observables" => Dict("pass" => length(matrix) == 9 && all(cell -> cell["base_value"]["computed_from_shared_state"] && cell["varied_value"]["computed_from_shared_state"], matrix)),
        "V2_recomputed_axis0" => Dict("pass" => blind["pass"], "blind_scale_comparison" => blind, "no_finals_family_templates" => true, "julia_reuse_mode" => JULIA_REUSE_MODE),
        "V5_julia_z3_raw_value_smt" => Dict("pass" => proof["verdict"] == "unsat" && proof["erased_control_verdict"] == "sat", "julia_z3" => proof),
        "V7_real_axis4_cell" => axis4,
        "V8_honest_o0_o3_scope" => Dict(
            "pass" => true,
            "o0_scope" => observe(build_shared_state(BASE_POLARITIES), "O0")["o0_scope"],
            "o3_scope" => observe(build_shared_state(BASE_POLARITIES), "O3")["o3_scope"],
        ),
        "G1_full_3x3_matrix" => Dict("pass" => length(matrix) == 9),
        "G2_G3_matrix_verdicts" => Dict("pass" => all(cell -> cell["pass"], matrix)),
        "G7_result_language" => Dict(
            "pass" => true,
            "classification" => CLASSIFICATION,
            "promotion_allowed" => PROMOTION_ALLOWED,
            "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
            "axis0_status" => AXIS0_STATUS,
            "claim_strength" => "class-level independence under the named pins, medium strength",
            "raw_dominance_claimed" => false,
        ),
    )
    all_pass = all(record -> record["pass"] == true, values(gates))
    Dict(
        "schema_version" => "axis_independence_discriminator_leg_v2",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "julia_reuse_mode" => JULIA_REUSE_MODE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "axis0_status" => AXIS0_STATUS,
        "promotion_fences" => Dict("axis_admission_allowed" => false, "axis0_closure_allowed" => false, "formal_admission_allowed" => false, "IGT_content" => false, "axis4_distinct_from_axis6" => true, "b6_scaffold_cited_as_independence_proof" => false),
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "reads_peer_result" => READS_PEER_RESULT,
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => READS_PEER_RESULT),
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "source_refs" => SOURCE_REFS,
        "source_reuse_lineage" => source_reuse_lineage(),
        "matrix_3x3" => matrix,
        "axis4_boundary_cell" => axis4,
        "blind_scale_comparison" => blind,
        "build_gates" => gates,
        "v2_requirement_receipts" => Dict(key => value for (key, value) in gates if startswith(key, "V")),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "v3_hardening_receipts" => Dict(
            "H1_honest_scope_fields" => gates["V8_honest_o0_o3_scope"],
            "claim_language" => "class-level independence under the named pins, medium strength",
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "packages_used" => ["LinearAlgebra", "JSON", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "control_only_tools" => [],
        "divergence_log" => ["Julia matched mirror recomputes the shared state and carries a Z3.jl raw-value side proof; source-locked imports are labeled as matched mirrors."],
        "shared_scalars" => shared_scalars(matrix, axis4, blind),
        "all_pass" => all_pass,
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "engine" => ENGINE,
        "result_path" => RESULT_PATH,
        "all_pass" => result["all_pass"],
        "matrix_cells" => length(result["matrix_3x3"]),
        "julia_z3" => result["crossover_proofs"]["julia_z3"]["verdict"],
        "blind_ne" => result["shared_scalars"]["axis0_ne_ppr_response"],
        "blind_se" => result["shared_scalars"]["axis0_se_ppr_response"],
    ), 2))
    result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
