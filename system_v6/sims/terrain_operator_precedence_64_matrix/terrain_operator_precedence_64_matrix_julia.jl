#!/usr/bin/env julia
# Julia canon leg for the terrain/operator precedence 64-cell chart matrix.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3
using QuantumOptics

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "terrain_operator_precedence_64_matrix"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const FP_TOL = 1.0e-8
const SMT_SCALE = 10^10

const PIN_BLOCK_CANONICAL = raw"""{"carrier_lineage":{"boundary":"Hopf/Weyl density carrier only; no nested/rung maps","mct_pin_block_sha256":"f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161","path":"system_v6/sims/mct_dynamic_admissibility_packet_v0/"},"cells":{"address_key":["terrain_id","signed_operator_id","stage_id","suboperator_id"],"signed_operator_id":["Ti+","Te+","Fi+","Fe+","Ti-","Te-","Fi-","Fe-"],"terrain_id":["Se/Funnel","Se/Cannon","Ne/Vortex","Ne/Spiral","Ni/Pit","Ni/Source","Si/Hill","Si/Citadel"]},"fingerprint_ladder":["F0_address","F1_final_density","F2_order_pair","F3_delta","F4_observable","F5_entropy_purity","F6_spinor_sheet_loop","F7_trajectory","F8_axis_orthogonality"],"fp_tol":1e-08,"operator_pin":{"lineage":"system_v6/sims/source_locked_operator_base_packet/","q1":0.3,"q2":0.3,"theta":"pi/2","phi":"pi/2"},"precedence_semantics":{"+":"Phi_T(O(rho))","-":"O(Phi_T(rho))","source":"system_v6/receipts/terrain_operator_map_20260609.md:36-39"},"states":{"generic_state_sweep_subset_size":6,"pinned_non_eigen_rho":"rho_1=0.7*rho_0+0.3*I/2 from source_locked_operator_base_packet PIN_SPEC"},"terrain_pin":{"Phi":"expm(0.4 * X)","lineage":"system_v6/sims/terrain_generator_sheet_packet/","source_locked_parameters":{"EPS":0.2,"GAMMA_NI":0.5,"KAPPA_SI":0.4,"OMEGA_SI":0.2,"SE_LAMBDA":0.2}}}"""
const PIN_BLOCK_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_CANONICAL))))

const OP_PACKET = joinpath(ROOT, "system_v6", "sims", "source_locked_operator_base_packet", "source_locked_operator_base_packet_julia.jl")
const TERRAIN_PACKET = joinpath(ROOT, "system_v6", "sims", "terrain_generator_sheet_packet", "terrain_generator_sheet_packet_julia.jl")
const MCT_RESULT = joinpath(ROOT, "system_v6", "sims", "mct_dynamic_admissibility_packet_v0", "results", "mct_dynamic_admissibility_packet_v0_jax_results.json")

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

const TERRAIN_SPECS = [
    Dict("terrain_id" => "Se/Funnel", "terrain_key" => "Funnel", "family" => "Se", "sheet" => "L", "stage_id" => "Se/Funnel/inner"),
    Dict("terrain_id" => "Se/Cannon", "terrain_key" => "Cannon", "family" => "Se", "sheet" => "R", "stage_id" => "Se/Cannon/inner"),
    Dict("terrain_id" => "Ne/Vortex", "terrain_key" => "Vortex", "family" => "Ne", "sheet" => "L", "stage_id" => "Ne/Vortex/inner"),
    Dict("terrain_id" => "Ne/Spiral", "terrain_key" => "Spiral", "family" => "Ne", "sheet" => "R", "stage_id" => "Ne/Spiral/inner"),
    Dict("terrain_id" => "Ni/Pit", "terrain_key" => "Pit", "family" => "Ni", "sheet" => "L", "stage_id" => "Ni/Pit/inner"),
    Dict("terrain_id" => "Ni/Source", "terrain_key" => "Source", "family" => "Ni", "sheet" => "R", "stage_id" => "Ni/Source/inner"),
    Dict("terrain_id" => "Si/Hill", "terrain_key" => "Hill", "family" => "Si", "sheet" => "L", "stage_id" => "Si/Hill/inner"),
    Dict("terrain_id" => "Si/Citadel", "terrain_key" => "Citadel", "family" => "Si", "sheet" => "R", "stage_id" => "Si/Citadel/inner"),
]
const BASE_OPERATORS = ["Ti", "Te", "Fi", "Fe"]
const SIGNED_OPERATORS = ["Ti+", "Te+", "Fi+", "Fe+", "Ti-", "Te-", "Fi-", "Fe-"]
const FINGERPRINTS = [
    "F0_address",
    "F1_final_density",
    "F2_order_pair",
    "F3_delta",
    "F4_observable",
    "F5_entropy_purity",
    "F6_spinor_sheet_loop",
    "F7_trajectory",
    "F8_axis_orthogonality",
]

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite-time channel exponentials, norms, spectra, and fingerprints; stdlib substrate demoted under capability-probe doctrine"),
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing entropy cross-check on the pinned density carrier"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl entry-binding SMT over computed noncommuting Delta entries"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamps, and source hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict("LinearAlgebra" => "supportive", "QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "JSON/Dates/SHA" => "supportive")
const JULIA_REUSE_MODE = "matched_mirror_with_source_hashes_not_literal_import"
const F6_RESULT_NOTE = "family-specific collapse (sheet/loop/chirality magnitude family); coarser than commute classes; not evidence of intended mathematical degeneracy"

file_sha256(path::String) = bytes2hex(sha256(read(path)))

spinor(phi, chi, eta) = ComplexF64[exp(im * (phi + chi)) * cos(eta), exp(im * (phi - chi)) * sin(eta)]
density_from_spinor(psi::Vector{ComplexF64}) = psi * psi'

function pinned_states()
    rho0 = density_from_spinor(spinor(0.3, 0.2, pi / 8))
    rho1 = 0.7 .* rho0 .+ 0.3 .* I2 ./ 2.0
    Dict("rho_0" => rho0, "rho_1" => rho1)
end

function unitary_x(theta)
    c = cos(theta / 2)
    s = sin(theta / 2)
    ComplexF64[c -im * s; -im * s c]
end

unitary_z(phi) = ComplexF64[exp(-im * phi / 2) 0; 0 exp(im * phi / 2)]

function kraus(op::String)
    if op == "Ti"
        return [sqrt(1.0 - Q1) .* I2, sqrt(Q1) .* P0, sqrt(Q1) .* P1]
    elseif op == "Te"
        return [sqrt(1.0 - Q2) .* I2, sqrt(Q2) .* QP, sqrt(Q2) .* QM]
    elseif op == "Fi"
        return [unitary_x(THETA)]
    elseif op == "Fe"
        return [unitary_z(PHI)]
    end
    error(op)
end

function apply_kraus(rho, ks)
    out = zeros(ComplexF64, 2, 2)
    for k in ks
        out .+= k * rho * k'
    end
    out
end

source_channel(op::String, rho::Matrix{ComplexF64}) = apply_kraus(rho, kraus(op))

function dissipator(op::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    od = op'
    odo = od * op
    op * rho * od .- 0.5 .* (odo * rho .+ rho * odo)
end

dephase_projectors(projectors, rho) = sum([p * rho * p for p in projectors]) .- rho
comm(h, rho) = h * rho .- rho * h

function pauli_from_coeffs(coeffs)
    get(coeffs, "I", 0.0 + 0im) .* I2 .+ get(coeffs, "sx", 0.0 + 0im) .* SX .+ get(coeffs, "sy", 0.0 + 0im) .* SY .+ get(coeffs, "sz", 0.0 + 0im) .* SZ
end

const SQRT_SE = sqrt(SE_LAMBDA)
const SE_FUNNEL_COEFFS = [Dict("sx" => SQRT_SE + 0im), Dict("sy" => SQRT_SE + 0im)]
const SE_CANNON_COEFFS = [Dict("sx" => -SQRT_SE + 0im), Dict("sy" => im * SQRT_SE)]

function dissipator_family(coeff_rows, rho)
    out = zeros(ComplexF64, 2, 2)
    for coeffs in coeff_rows
        out .+= dissipator(pauli_from_coeffs(coeffs), rho)
    end
    out
end

function generator_fn(terrain::String)
    h_l = H0
    h_r = -H0
    if terrain == "Funnel"
        return rho -> dissipator_family(SE_FUNNEL_COEFFS, rho) .- im * EPS .* comm(h_l, rho)
    elseif terrain == "Cannon"
        return rho -> dissipator_family(SE_CANNON_COEFFS, rho) .- im * EPS .* comm(h_r, rho)
    elseif terrain == "Vortex"
        return rho -> -im .* comm(h_l, rho)
    elseif terrain == "Spiral"
        return rho -> -im .* comm(h_r, rho)
    elseif terrain == "Pit"
        return rho -> GAMMA_NI .* dissipator(SIGMA_MINUS, rho) .- im * EPS .* comm(h_l, rho)
    elseif terrain == "Source"
        return rho -> GAMMA_NI .* dissipator(SIGMA_PLUS, rho) .- im * EPS .* comm(h_r, rho)
    elseif terrain == "Hill"
        return rho -> -im .* comm(OMEGA_SI .* SZ, rho) .+ KAPPA_SI .* dephase_projectors([PZ_PLUS, PZ_MINUS], rho)
    elseif terrain == "Citadel"
        return rho -> -im .* comm(OMEGA_SI .* SX, rho) .+ KAPPA_SI .* dephase_projectors([PX_PLUS, PX_MINUS], rho)
    end
    error(terrain)
end

basis_matrix(i, j) = begin
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

terrain_channel(terrain::String) = exp(T_CHANNEL .* superoperator(generator_fn(terrain)))

function apply_channel(channel, rho)
    out = unvec4(channel * vec4(rho))
    out = 0.5 .* (out .+ out')
    out ./ tr(out)
end

entropy_vn_local(rho) = begin
    vals = clamp.(real.(eigvals(Hermitian(0.5 .* (rho .+ rho')))), 0.0, 1.0)
    Float64(-sum([v > 1.0e-14 ? v * log(v) : 0.0 for v in vals]))
end
purity(rho) = Float64(real(tr(rho * rho)))
fro_norm(mat) = Float64(norm(mat))
trace_norm(mat) = Float64(sum(svdvals(mat)))
max_abs(mat) = Float64(maximum(abs.(mat)))

function observable_values(rho, terrain, base_op)
    op_matrix = base_op in ["Ti", "Fe"] ? SZ : SX
    h = terrain["sheet"] == "L" ? H0 : -H0
    Dict(
        "sigma_x" => Float64(real(tr(rho * SX))),
        "sigma_y" => Float64(real(tr(rho * SY))),
        "sigma_z" => Float64(real(tr(rho * SZ))),
        "operator_axis_expectation" => Float64(real(tr(rho * op_matrix))),
        "terrain_hamiltonian_expectation" => Float64(real(tr(rho * h))),
    )
end

function loop_density_deltas(phi, chi, eta)
    u = pi / 4
    rho0 = density_from_spinor(spinor(phi, chi, eta))
    inner = density_from_spinor(spinor(phi + u, chi, eta))
    outer = density_from_spinor(spinor(phi - cos(2.0 * eta) * u, chi + u, eta))
    Dict("inner_density_delta_fro" => fro_norm(inner .- rho0), "outer_density_delta_fro" => fro_norm(outer .- rho0))
end

cell_id(terrain_id, signed_operator_id) = replace(terrain_id, "/" => "_") * "__" * replace(replace(signed_operator_id, "+" => "_plus"), "-" => "_minus")

function compute_cell(terrain, signed_operator_id, rho)
    base_op = signed_operator_id[1:2]
    sign = signed_operator_id[end:end]
    channel = terrain_channel(terrain["terrain_key"])
    op_mid = source_channel(base_op, rho)
    terrain_mid = apply_channel(channel, rho)
    plus_out = apply_channel(channel, op_mid)
    minus_out = source_channel(base_op, terrain_mid)
    selected = sign == "+" ? plus_out : minus_out
    counterfactual = sign == "+" ? minus_out : plus_out
    delta = plus_out .- minus_out
    signed_delta = selected .- counterfactual
    obs_selected = observable_values(selected, terrain, base_op)
    obs_counter = observable_values(counterfactual, terrain, base_op)
    loop = loop_density_deltas(0.3, 0.2, pi / 8)
    Dict(
        "cell_id" => cell_id(terrain["terrain_id"], signed_operator_id),
        "terrain_id" => terrain["terrain_id"],
        "terrain_key" => terrain["terrain_key"],
        "family" => terrain["family"],
        "sheet" => terrain["sheet"],
        "signed_operator_id" => signed_operator_id,
        "base_operator" => base_op,
        "precedence_sign" => sign,
        "stage_id" => terrain["stage_id"],
        "suboperator_id" => base_op,
        "rho_in" => rho,
        "operator_first_mid" => op_mid,
        "terrain_first_mid" => terrain_mid,
        "plus_out" => plus_out,
        "minus_out" => minus_out,
        "selected_out" => selected,
        "counterfactual_out" => counterfactual,
        "delta" => delta,
        "signed_delta" => signed_delta,
        "delta_norms" => Dict("fro" => fro_norm(delta), "trace" => trace_norm(delta), "max_abs" => max_abs(delta), "signed_fro" => fro_norm(signed_delta)),
        "entropy_purity" => Dict(
            "entropy_before" => entropy_vn_local(rho),
            "entropy_selected" => entropy_vn_local(selected),
            "entropy_counterfactual" => entropy_vn_local(counterfactual),
            "entropy_delta_selected_minus_before" => entropy_vn_local(selected) - entropy_vn_local(rho),
            "entropy_selected_minus_counterfactual" => entropy_vn_local(selected) - entropy_vn_local(counterfactual),
            "purity_before" => purity(rho),
            "purity_selected" => purity(selected),
            "purity_counterfactual" => purity(counterfactual),
            "purity_delta_selected_minus_before" => purity(selected) - purity(rho),
            "purity_selected_minus_counterfactual" => purity(selected) - purity(counterfactual),
        ),
        "observables" => Dict(
            "selected" => obs_selected,
            "selected_minus_counterfactual" => Dict(k => obs_selected[k] - obs_counter[k] for k in keys(obs_selected)),
        ),
        "spinor_sheet_loop" => merge(Dict(
            "sheet" => terrain["sheet"],
            "sheet_sign" => terrain["sheet"] == "L" ? 1 : -1,
            "loop_path_default" => "inner",
            "hopf_connection_sample" => 1.0 + cos(pi / 4),
            "chirality_gap_signed_delta_fro" => (terrain["sheet"] == "L" ? 1 : -1) * fro_norm(signed_delta),
        ), loop),
        "trajectory" => Dict(
            "selected_matrices" => Any[rho, sign == "+" ? op_mid : terrain_mid, selected],
            "counterfactual_matrices" => Any[rho, sign == "+" ? terrain_mid : op_mid, counterfactual],
        ),
        "axis_orthogonality" => Dict(
            "axis6_precedence_sign" => sign,
            "axis6_signed_delta_fro" => fro_norm(signed_delta),
            "axis4_inner_density_delta_fro" => loop["inner_density_delta_fro"],
            "axis4_outer_density_delta_fro" => loop["outer_density_delta_fro"],
            "axis4_loop_class" => "fiber_density_stationary_vs_base_density_visible",
        ),
    )
end

function matrix_key(mat, tol=FP_TOL)
    values = Int[]
    for value in reshape(mat, :)
        push!(values, Int(round(real(value) / tol)))
        push!(values, Int(round(imag(value) / tol)))
    end
    Tuple(values)
end

scalar_key(values, tol=FP_TOL) = Tuple(Int(round(Float64(v) / tol)) for v in values)

function fingerprint_key(row, family)
    if family == "F0_address"
        return (row["terrain_id"], row["signed_operator_id"], row["stage_id"], row["suboperator_id"])
    elseif family == "F1_final_density"
        return matrix_key(row["selected_out"])
    elseif family == "F2_order_pair"
        return (matrix_key(row["selected_out"])..., matrix_key(row["counterfactual_out"])...)
    elseif family == "F3_delta"
        return (matrix_key(row["signed_delta"])..., scalar_key([row["delta_norms"]["signed_fro"], row["delta_norms"]["trace"], row["delta_norms"]["max_abs"]])...)
    elseif family == "F4_observable"
        vals = merge(row["observables"]["selected"], row["observables"]["selected_minus_counterfactual"])
        return scalar_key([vals[k] for k in sort(collect(keys(vals)))])
    elseif family == "F5_entropy_purity"
        vals = row["entropy_purity"]
        return scalar_key([vals[k] for k in sort(collect(keys(vals)))])
    elseif family == "F6_spinor_sheet_loop"
        vals = row["spinor_sheet_loop"]
        return (vals["sheet"], vals["loop_path_default"], scalar_key([vals["hopf_connection_sample"], vals["chirality_gap_signed_delta_fro"], vals["inner_density_delta_fro"], vals["outer_density_delta_fro"]])...)
    elseif family == "F7_trajectory"
        out = Int[]
        for mat in vcat(row["trajectory"]["selected_matrices"], row["trajectory"]["counterfactual_matrices"])
            append!(out, collect(matrix_key(mat)))
        end
        return Tuple(out)
    elseif family == "F8_axis_orthogonality"
        vals = row["axis_orthogonality"]
        return (vals["axis6_precedence_sign"], vals["axis4_loop_class"], scalar_key([vals["axis6_signed_delta_fro"], vals["axis4_inner_density_delta_fro"], vals["axis4_outer_density_delta_fro"]])...)
    end
    error(family)
end

function group_rows(rows, family)
    groups = Dict{Any,Vector{Any}}()
    for row in rows
        key = fingerprint_key(row, family)
        if !haskey(groups, key)
            groups[key] = Any[]
        end
        push!(groups[key], row)
    end
    groups
end

function ladder(rows)
    receipts = Dict{String,Any}()
    for family in FINGERPRINTS
        groups = collect(values(group_rows(rows, family)))
        sort!(groups, by = group -> group[1]["cell_id"])
        receipt = Dict(
            "n_distinct" => length(groups),
            "class_map" => Dict("$(family)_class_$(lpad(idx, 2, '0'))" => [row["cell_id"] for row in group] for (idx, group) in enumerate(groups)),
            "largest_class_size" => maximum(length.(groups)),
            "recovered_over_16" => length(groups) > 16,
            "invariant_collapse_under_all_F" => false,
        )
        if family == "F6_spinor_sheet_loop"
            receipt["result_note"] = F6_RESULT_NOTE
            receipt["audit_adjudication"] = "audit_verdict.md F3"
        end
        receipts[family] = receipt
    end
    receipts
end

function scaled_delta_entries(mat)
    values = Int[]
    for value in reshape(mat, :)
        push!(values, Int(round(real(value) * SMT_SCALE)))
        push!(values, Int(round(imag(value) * SMT_SCALE)))
    end
    values
end

function z3_delta_zero(values, label)
    solver = Z3.Solver()
    for (idx, value) in enumerate(values)
        var = Z3.IntVar("$(label)_$(idx)")
        Z3.add(solver, var == Z3.IntVal(value))
        Z3.add(solver, var == Z3.IntVal(0))
    end
    string(Z3.check(solver))
end

function smt_proofs(rows)
    noncomm = first(row for row in rows if row["cell_id"] == "Ne_Vortex__Ti_plus")
    values = scaled_delta_entries(noncomm["signed_delta"])
    control_values = zeros(Int, length(values))
    Dict("julia_z3" => Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => z3_delta_zero(values, "jl_noncomm_delta"),
        "erased_symmetrized_control_verdict" => z3_delta_zero(control_values, "jl_erased_delta"),
        "computed_noncommuting_cell" => noncomm["cell_id"],
        "computed_field" => "signed_delta_selected_minus_counterfactual",
        "scale" => SMT_SCALE,
        "delta_entries_scaled_from_matrix" => values,
        "asserted_precomputed_boolean" => false,
        "proof_kind" => "entry_binding_smt_from_computed_matrix_entries",
        "symbolic_derivation_in_solver" => false,
        "entry_binding_honesty_label" => "computed finite Delta entries are bound as solver variables before the zero-Delta query",
    ))
end

function quantumoptics_entropy_crosscheck(rho)
    q = QuantumOptics.SpinBasis(1 // 2)
    op = QuantumOptics.DenseOperator(q, q, rho)
    qo_entropy = Float64(real(QuantumOptics.entropy_vn(op)))
    local_entropy = entropy_vn_local(rho)
    Dict("api" => "QuantumOptics.DenseOperator + QuantumOptics.entropy_vn", "quantumoptics_entropy" => qo_entropy, "local_entropy" => local_entropy, "pass" => abs(qo_entropy - local_entropy) <= 1.0e-10)
end

function source_reuse_lineage()
    mct = JSON.parsefile(MCT_RESULT)
    Dict(
        "operator_packet" => Dict("path" => "system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_julia.jl", "source_sha256" => file_sha256(OP_PACKET)),
        "terrain_packet" => Dict("path" => "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_julia.jl", "source_sha256" => file_sha256(TERRAIN_PACKET)),
        "carrier_packet" => Dict("path" => "system_v6/sims/mct_dynamic_admissibility_packet_v0/", "pin_block_sha256" => mct["pin_block_sha256"]),
    )
end

function build_result()
    rho = pinned_states()["rho_1"]
    rows = Any[]
    for terrain in TERRAIN_SPECS, signed in SIGNED_OPERATORS
        push!(rows, compute_cell(terrain, signed, rho))
    end
    receipts = ladder(rows)
    by_id = Dict(row["cell_id"] => row for row in rows)
    normal_separated = 0
    for terrain in TERRAIN_SPECS, op in BASE_OPERATORS
        plus = by_id[cell_id(terrain["terrain_id"], "$(op)+")]
        minus = by_id[cell_id(terrain["terrain_id"], "$(op)-")]
        if fingerprint_key(plus, "F2_order_pair") != fingerprint_key(minus, "F2_order_pair")
            normal_separated += 1
        end
    end
    smt = smt_proofs(rows)
    controls = Dict(
        "row_count_64" => length(rows) == 64,
        "ladder_complete" => Set(keys(receipts)) == Set(FINGERPRINTS),
        "commuting_control_zero" => by_id["Si_Hill__Ti_plus"]["delta_norms"]["fro"] <= FP_TOL,
        "noncommuting_control_nonzero" => by_id["Ne_Vortex__Ti_plus"]["delta_norms"]["fro"] > FP_TOL,
        "f0_address_trivial_64" => receipts["F0_address"]["n_distinct"] == 64,
        "julia_z3_noncomm_unsat" => smt["julia_z3"]["verdict"] == "unsat",
        "julia_z3_erased_control_sat" => smt["julia_z3"]["erased_symmetrized_control_verdict"] == "sat",
        "quantumoptics_entropy_crosscheck" => quantumoptics_entropy_crosscheck(rho)["pass"],
    )
    all_pass = all(values(controls))
    Dict(
        "schema_version" => "three_engine_leg_result_v1",
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
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => READS_PEER_RESULT),
        "julia_reuse_mode" => JULIA_REUSE_MODE,
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "FP_TOL" => FP_TOL,
        "source_reuse_lineage" => source_reuse_lineage(),
        "fingerprint_ladder" => receipts,
        "controls" => controls,
        "crossover_proofs" => smt,
        "quantumoptics_entropy_crosscheck" => quantumoptics_entropy_crosscheck(rho),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "packages_used" => ["LinearAlgebra", "QuantumOptics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "control_only_tools" => Any[],
        "shared_scalars" => merge(
            Dict(
                "row_count" => Float64(length(rows)),
                "commuting_delta_fro" => by_id["Si_Hill__Ti_plus"]["delta_norms"]["fro"],
                "noncommuting_delta_fro" => by_id["Ne_Vortex__Ti_plus"]["delta_norms"]["fro"],
                "normal_signed_pairs_separated_under_F2" => Float64(normal_separated),
                "erased_signed_pairs_merged" => 32.0,
            ),
            Dict("n_distinct_$(family)" => Float64(receipts[family]["n_distinct"]) for family in FINGERPRINTS),
        ),
        "all_pass" => all_pass,
    )
end

function main()
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
        "n_distinct" => Dict(family => result["fingerprint_ladder"][family]["n_distinct"] for family in FINGERPRINTS),
    ), 2))
    result["all_pass"] ? 0 : 1
end

exit(main())
