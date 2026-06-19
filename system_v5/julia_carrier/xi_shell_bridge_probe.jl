#!/usr/bin/env julia
# object_id: xi_shell_bridge_probe
# classification: scratch_diagnostic
# fence: formal_scout/scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite Xi_shell bridge object plus flat-geometry kill control only.
# No Axis0, gravity, physics, bridge-admission, FEP, consciousness, or formal admission claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "xi_shell_bridge_probe"
const RESULT_PATH = joinpath(@__DIR__, "xi_shell_bridge_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "xi_shell_bridge_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const ENTROPY_EPS = 1.0e-12
const J_COUNT = 3
const K_COUNT = 3
const REMOTE_EDIT_PAIR = (3, 2)
const REMOTE_EDIT_DELTA = 1.137

const BLOCKED_CONSUMERS = [
    "Axis0-admission",
    "gravity",
    "physics",
    "bridge-admission",
    "FEP",
    "consciousness",
    "formal-admission",
]

const I2 = ComplexF64[1 0; 0 1]

pair_key(j::Int, k::Int) = string(j, ",", k)
branch_pairs() = [(j, k) for j in 1:J_COUNT for k in 1:K_COUNT]
linf_matrix(a::AbstractMatrix, b::AbstractMatrix) = maximum(abs.(a .- b))

function spinor(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
end

function spinor_perp(theta::Float64, phi::Float64)
    ComplexF64[-exp(-im * phi) * sin(theta / 2.0), cos(theta / 2.0)]
end

function bloch_vector(theta::Float64, phi::Float64)
    [sin(theta) * cos(phi), sin(theta) * sin(phi), cos(theta)]
end

function density(psi::Vector{ComplexF64})
    v = psi ./ norm(psi)
    v * v'
end

function branch_weights()
    raw = Float64[]
    for (j, k) in branch_pairs()
        push!(raw, 1.0 + Float64(mod(17 * j + 29 * k + 11 * j * k, 13)) / 7.0 + 0.05 * j + 0.03 * k)
    end
    raw ./ sum(raw)
end

function scrambled_weights(weights::Vector{Float64})
    weights[reverse(1:length(weights))]
end

function nested_hopf_frame(j::Int, k::Int, weight::Float64)
    eta = pi * (Float64(j) + 0.17 * Float64(k)) / (2.0 * (Float64(J_COUNT) + 1.0))
    phi = 2.0 * pi * Float64(mod(2 * j + k, J_COUNT * K_COUNT)) / Float64(J_COUNT * K_COUNT) + 0.07 * k
    chi = 2.0 * pi * Float64(mod(j + 2 * k + 1, 11)) / 11.0 + 0.11 * j
    base = [
        sin(2.0 * eta) * cos(phi + chi),
        sin(2.0 * eta) * sin(phi + chi),
        cos(2.0 * eta),
    ]
    fiber = [cos(phi - chi), sin(phi - chi), cos(2.0 * eta)]
    fiber = fiber ./ norm(fiber)
    gamma = clamp(dot(base, fiber), -1.0, 1.0)
    lambda = 0.5 + 0.24 * tanh(1.2 * gamma)
    theta_a = 2.0 * eta
    phi_a = phi + chi
    theta_b = acos(clamp(fiber[3], -1.0, 1.0))
    phi_b = atan(fiber[2], fiber[1])
    phase = (phi - chi) + 0.5 * base[2]
    Dict{String,Any}(
        "geometry" => "nested_hopf_tori",
        "j" => j,
        "k" => k,
        "weight" => weight,
        "eta" => eta,
        "phi" => phi,
        "chi" => chi,
        "theta_a" => theta_a,
        "phi_a" => phi_a,
        "theta_b" => theta_b,
        "phi_b" => phi_b,
        "gamma" => gamma,
        "lambda" => lambda,
        "phase" => phase,
        "hopf_base" => base,
        "fiber_axis" => fiber,
    )
end

function flat_product_frame(j::Int, k::Int, weight::Float64)
    theta_a = pi * Float64(j) / Float64(J_COUNT + 1)
    phi_a = 2.0 * pi * Float64(k) / Float64(K_COUNT) + 0.13 * j
    theta_b = pi * Float64(k) / Float64(K_COUNT + 1)
    phi_b = 2.0 * pi * Float64(j) / Float64(J_COUNT) + 0.17 * k
    a_axis = bloch_vector(theta_a, phi_a)
    b_axis = bloch_vector(theta_b, phi_b)
    gamma = clamp(dot(a_axis, b_axis), -1.0, 1.0)
    lambda = 0.5 + 0.24 * tanh(1.2 * gamma)
    phase = phi_a - phi_b
    Dict{String,Any}(
        "geometry" => "flat_s2_product",
        "j" => j,
        "k" => k,
        "weight" => weight,
        "theta_a" => theta_a,
        "phi_a" => phi_a,
        "theta_b" => theta_b,
        "phi_b" => phi_b,
        "gamma" => gamma,
        "lambda" => lambda,
        "phase" => phase,
        "a_axis" => a_axis,
        "b_axis" => b_axis,
        "flat_control_note" => "two independent S2 spinor frames; no S3 eta/fiber coordinate",
    )
end

function frame_for(geometry::String, j::Int, k::Int, weight::Float64)
    geometry == "nested_hopf_tori" && return nested_hopf_frame(j, k, weight)
    geometry == "flat_s2_product" && return flat_product_frame(j, k, weight)
    error("unknown geometry: $geometry")
end

function rho_from_frame(frame::Dict{String,Any}; remote_delta::Float64 = 0.0)
    a = spinor(Float64(frame["theta_a"]), Float64(frame["phi_a"]))
    ap = spinor_perp(Float64(frame["theta_a"]), Float64(frame["phi_a"]))
    b = spinor(Float64(frame["theta_b"]), Float64(frame["phi_b"]) + remote_delta)
    bp = spinor_perp(Float64(frame["theta_b"]), Float64(frame["phi_b"]) + remote_delta)
    lambda = Float64(frame["lambda"])
    phase = Float64(frame["phase"])
    psi = sqrt(lambda) .* kron(a, b) .+ exp(im * phase) * sqrt(1.0 - lambda) .* kron(ap, bp)
    density(psi)
end

function product_rho_from_frame(frame::Dict{String,Any})
    a = spinor(pi / 3.0, 0.21)
    b = spinor(Float64(frame["theta_b"]), Float64(frame["phi_b"]))
    density(kron(a, b))
end

function partial_trace_a(rho::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for a in 0:1, ap in 0:1, b in 0:1
        out[a + 1, ap + 1] += rho[2 * a + b + 1, 2 * ap + b + 1]
    end
    out
end

function partial_trace_b(rho::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for b in 0:1, bp in 0:1, a in 0:1
        out[b + 1, bp + 1] += rho[2 * a + b + 1, 2 * a + bp + 1]
    end
    out
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    herm = Hermitian((rho + rho') ./ 2.0)
    vals = eigvals(herm)
    entropy = 0.0
    for v in vals
        p = max(real(v), 0.0)
        p > ENTROPY_EPS && (entropy -= p * log2(p))
    end
    entropy
end

function effective_rank(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho + rho') ./ 2.0))
    count(v -> real(v) > TOL, vals)
end

function readout(rho::Matrix{ComplexF64})
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho)
    Dict{String,Any}(
        "S_A" => s_a,
        "S_B" => s_b,
        "S_AB" => s_ab,
        "S_A_given_B" => s_ab - s_b,
        "I_c_A_to_B" => s_b - s_ab,
        "I_A_B" => s_a + s_b - s_ab,
        "purity" => real(tr(rho * rho)),
        "effective_rank" => effective_rank(rho),
    )
end

function density_diagnostics(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian((rho + rho') ./ 2.0))
    Dict{String,Any}(
        "trace_residual" => abs(real(tr(rho)) - 1.0),
        "hermitian_residual" => norm(rho - rho'),
        "min_eigenvalue" => minimum(real.(vals)),
        "purity" => real(tr(rho * rho)),
    )
end

function xi_for_geometry(geometry::String, weights::Vector{Float64};
        product_cut::Bool = false,
        one_future_pair::Union{Nothing,Tuple{Int,Int}} = nothing,
        remote_edit_pair::Union{Nothing,Tuple{Int,Int}} = nothing,
        remote_delta::Float64 = 0.0)
    xi = zeros(ComplexF64, 4, 4)
    frames = Vector{Dict{String,Any}}()
    rhos = Dict{String,Matrix{ComplexF64}}()
    branch_diag = Vector{Dict{String,Any}}()
    pairs = branch_pairs()
    for (idx, (j, k)) in enumerate(pairs)
        w = isnothing(one_future_pair) ? weights[idx] : ((j, k) == one_future_pair ? 1.0 : 0.0)
        frame = frame_for(geometry, j, k, w)
        delta = (!isnothing(remote_edit_pair) && (j, k) == remote_edit_pair) ? remote_delta : 0.0
        rho = product_cut ? product_rho_from_frame(frame) : rho_from_frame(frame; remote_delta = delta)
        xi .+= w .* rho
        push!(frames, frame)
        rhos[pair_key(j, k)] = rho
        diag = density_diagnostics(rho)
        push!(branch_diag, Dict{String,Any}(
            "j" => j,
            "k" => k,
            "weight" => w,
            "gamma" => frame["gamma"],
            "lambda" => frame["lambda"],
            "trace_residual" => diag["trace_residual"],
            "hermitian_residual" => diag["hermitian_residual"],
            "min_eigenvalue" => diag["min_eigenvalue"],
        ))
    end
    xi_diag = density_diagnostics(xi)
    Dict{String,Any}(
        "geometry" => geometry,
        "xi" => xi,
        "frames" => frames,
        "branch_rhos" => rhos,
        "branch_diagnostics" => branch_diag,
        "xi_diagnostics" => xi_diag,
        "readout" => readout(xi),
    )
end

function readout_delta(a::Dict{String,Any}, b::Dict{String,Any})
    keys = ["I_c_A_to_B", "S_A_given_B", "I_A_B"]
    diffs = Dict{String,Any}()
    max_diff = 0.0
    for key in keys
        diff = abs(Float64(a[key]) - Float64(b[key]))
        diffs[key] = diff
        max_diff = max(max_diff, diff)
    end
    diffs["max"] = max_diff
    diffs
end

function weighted_signature(frames::Vector{Dict{String,Any}})
    total = sum(Float64(f["weight"]) for f in frames)
    [
        sum(Float64(f["weight"]) * Float64(f["gamma"]) for f in frames) / total,
        sum(Float64(f["weight"]) * Float64(f["lambda"]) for f in frames) / total,
        sum(Float64(f["weight"]) * cos(Float64(f["phase"])) for f in frames) / total,
        sum(Float64(f["weight"]) * sin(Float64(f["phase"])) for f in frames) / total,
    ]
end

function ftl_message_check(weights::Vector{Float64})
    base = xi_for_geometry("nested_hopf_tori", weights)
    edited = xi_for_geometry("nested_hopf_tori", weights; remote_edit_pair = REMOTE_EDIT_PAIR, remote_delta = REMOTE_EDIT_DELTA)
    key = pair_key(REMOTE_EDIT_PAIR[1], REMOTE_EDIT_PAIR[2])
    branch_a_diff = linf_matrix(partial_trace_a(base["branch_rhos"][key]), partial_trace_a(edited["branch_rhos"][key]))
    global_a_diff = linf_matrix(partial_trace_a(base["xi"]), partial_trace_a(edited["xi"]))
    global_readout_delta = readout_delta(base["readout"], edited["readout"])
    leak = branch_a_diff > TOL || global_a_diff > TOL
    Dict{String,Any}(
        "remote_edit_pair" => [REMOTE_EDIT_PAIR[1], REMOTE_EDIT_PAIR[2]],
        "remote_edit_delta" => REMOTE_EDIT_DELTA,
        "branch_rho_A_linf_diff" => branch_a_diff,
        "global_rho_A_linf_diff" => global_a_diff,
        "global_readout_delta" => global_readout_delta,
        "global_readout_changed" => global_readout_delta["max"] > STRICT_STOP_TOL,
        "remote_marginal_invariant" => !leak,
        "controllable_ftl_message_capacity" => leak ? 1.0 : 0.0,
        "verdict" => leak ? "LEAK_FALSIFIES_MODEL" : "ZERO_CONTROLLABLE_MESSAGE",
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
        )
    end
    peer = JSON.parsefile(peer_path)
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer_scalars[key])
        diff = abs(jv - pv)
        diff > max_diff && (max_diff = diff; max_diff_key = key)
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
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
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function scalarize_readout(prefix::String, readout_dict::Dict{String,Any})
    Dict{String,Any}(
        prefix * ".I_c_A_to_B" => readout_dict["I_c_A_to_B"],
        prefix * ".S_A_given_B" => readout_dict["S_A_given_B"],
        prefix * ".I_A_B" => readout_dict["I_A_B"],
        prefix * ".S_AB" => readout_dict["S_AB"],
        prefix * ".purity" => readout_dict["purity"],
        prefix * ".effective_rank" => Float64(readout_dict["effective_rank"]),
    )
end

function build_result()
    weights = branch_weights()
    nested = xi_for_geometry("nested_hopf_tori", weights)
    flat = xi_for_geometry("flat_s2_product", weights)
    scrambled = xi_for_geometry("nested_hopf_tori", scrambled_weights(weights))
    one_future = xi_for_geometry("nested_hopf_tori", weights; one_future_pair = (2, 2))
    product_cut = xi_for_geometry("nested_hopf_tori", weights; product_cut = true)
    ftl = ftl_message_check(weights)

    geometry_delta = readout_delta(nested["readout"], flat["readout"])
    scrambled_delta = readout_delta(nested["readout"], scrambled["readout"])
    product_ic_abs = abs(Float64(product_cut["readout"]["I_c_A_to_B"]))
    one_future_degenerate = Int(one_future["readout"]["effective_rank"]) == 1 &&
        abs(Float64(one_future["readout"]["S_AB"])) < TOL

    nested_signature = weighted_signature(nested["frames"])
    flat_signature = weighted_signature(flat["frames"])
    geometry_signature_l2 = norm(nested_signature .- flat_signature)
    flat_same_to_machine = geometry_delta["max"] < TOL
    geometry_verdict = flat_same_to_machine ? "KILLED_BY_FLAT_CONTROL" : "SURVIVED_CANDIDATE_ONLY"
    xi_geometry_load_bearing = flat_same_to_machine ? "FALSE" : "SURVIVED (candidate only)"

    controls = Dict{String,Any}(
        "flat_geometry_is_distinct" => geometry_signature_l2 > STRICT_STOP_TOL,
        "scrambled_Omega_changes_readout" => scrambled_delta["max"] > STRICT_STOP_TOL,
        "one_future_degenerates" => one_future_degenerate,
        "product_no_entanglement_cut_Ic_zero" => product_ic_abs < TOL,
        "zero_controllable_message" => ftl["controllable_ftl_message_capacity"] == 0.0,
    )

    verdicts = Dict{String,Any}(
        "xi_geometry_load_bearing_candidate" => !flat_same_to_machine,
        "flat_control_killed_geometry_load_bearing" => flat_same_to_machine,
        "kill_control_valid" => controls["flat_geometry_is_distinct"],
        "controls_pass" => all(Bool(v) for v in values(controls)),
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
    )

    shared_scalars = Dict{String,Any}()
    merge!(shared_scalars, scalarize_readout("nested", nested["readout"]))
    merge!(shared_scalars, scalarize_readout("flat", flat["readout"]))
    merge!(shared_scalars, scalarize_readout("scrambled", scrambled["readout"]))
    merge!(shared_scalars, scalarize_readout("one_future", one_future["readout"]))
    merge!(shared_scalars, scalarize_readout("product_cut", product_cut["readout"]))
    shared_scalars["nested_flat_delta.I_c_A_to_B"] = geometry_delta["I_c_A_to_B"]
    shared_scalars["nested_flat_delta.S_A_given_B"] = geometry_delta["S_A_given_B"]
    shared_scalars["nested_flat_delta.I_A_B"] = geometry_delta["I_A_B"]
    shared_scalars["nested_flat_delta.max"] = geometry_delta["max"]
    shared_scalars["scrambled_delta.max"] = scrambled_delta["max"]
    shared_scalars["product_cut.I_c_abs"] = product_ic_abs
    shared_scalars["geometry_signature_l2"] = geometry_signature_l2
    shared_scalars["ftl.branch_rho_A_linf_diff"] = ftl["branch_rho_A_linf_diff"]
    shared_scalars["ftl.global_rho_A_linf_diff"] = ftl["global_rho_A_linf_diff"]
    shared_scalars["ftl.global_readout_delta.max"] = ftl["global_readout_delta"]["max"]
    shared_scalars["ftl.controllable_message_capacity"] = ftl["controllable_ftl_message_capacity"]

    shared_booleans = Dict{String,Any}()
    for (key, value) in controls
        shared_booleans["control.$key"] = value
    end
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "fence" => "formal_scout/scratch_diagnostic",
        "promotion_allowed" => false,
        "PROMOTION_ALLOWED" => false,
        "formal_admission_allowed" => false,
        "FORMAL_ADMISSION_ALLOWED" => false,
        "claim_ceiling" => "Finite Xi_shell bridge object and kill controls only; no Axis0, gravity, physics, bridge-admission, FEP, consciousness, or formal admission claim.",
        "sim_execution_kind" => "bridge",
        "sim_class" => "xi_shell_bridge_flat_geometry_kill_control_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "eligible_consumers" => ["formal_scout_review_only"],
        "allowed_claims" => ["finite Xi_fuzz cut object exists in this probe", "flat geometry kill control result for this finite construction", "zero-controllable-message diagnostic for the branch edit tested"],
        "geometry_control" => Dict{String,Any}(
            "nested" => "S3 nested Hopf torus frame z=cos(eta)e^{i phi}, w=sin(eta)e^{i chi}; base/fiber feed Weyl/gamma state construction",
            "flat" => "plain product of two independent S2 spinor frames; same gamma-to-lambda and rho_AB construction, no S3 eta/fiber",
            "same_weights_for_nested_and_flat" => true,
            "geometry_signature_l2" => geometry_signature_l2,
        ),
        "branch_weights" => weights,
        "fuzz_field" => Dict{String,Any}(
            "index_set" => [[j, k] for (j, k) in branch_pairs()],
            "weight_rule" => "normalized positive finite compatibility weights over (j,k); identical for nested and flat kill control",
            "Xi_fuzz" => "sum_jk p(j,k) rho_AB(j,k)",
            "axis0_readout_names_only" => ["I_c_A_to_B", "S_A_given_B", "I_A_B"],
        ),
        "xi_geometry_load_bearing" => xi_geometry_load_bearing,
        "geometry_load_bearing_verdict" => geometry_verdict,
        "nested_readout" => nested["readout"],
        "flat_readout" => flat["readout"],
        "nested_flat_delta" => geometry_delta,
        "scrambled_Omega_control" => Dict{String,Any}("readout" => scrambled["readout"], "delta_from_nested" => scrambled_delta),
        "one_future_control" => Dict{String,Any}("selected_branch" => [2, 2], "readout" => one_future["readout"], "degenerate" => one_future_degenerate),
        "product_no_entanglement_cut" => Dict{String,Any}("readout" => product_cut["readout"], "I_c_abs" => product_ic_abs),
        "ftl_message_capacity_check" => ftl,
        "controls" => controls,
        "verdicts" => verdicts,
        "nested_branch_diagnostics" => nested["branch_diagnostics"],
        "flat_branch_diagnostics" => flat["branch_diagnostics"],
        "xi_diagnostics" => Dict{String,Any}(
            "nested" => nested["xi_diagnostics"],
            "flat" => flat["xi_diagnostics"],
            "scrambled" => scrambled["xi_diagnostics"],
            "one_future" => one_future["xi_diagnostics"],
            "product_cut" => product_cut["xi_diagnostics"],
        ),
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing finite branch map, density matrices, controls, and result synthesis",
            "LinearAlgebra" => "load-bearing partial traces, eigenspectra, entropies, norms, and parity scalars",
            "JSON" => "supportive result serialization",
        ),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia" => "load-bearing finite branch map, density matrices, controls, and result synthesis",
            "LinearAlgebra" => "load-bearing partial traces, eigenspectra, entropies, norms, and parity scalars",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}("Julia" => "load_bearing", "LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}("Julia" => "load_bearing", "LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
        "divergence_log" => ["flat_s2_product kill control compared against nested_hopf_tori with identical branch weights", "scrambled_Omega, one_future, product_no_entanglement_cut, and remote-branch FTL controls run"],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "This is only a finite Xi_shell bridge falsifier: it computes Xi_fuzz readouts on nested-Hopf versus flat S2-product geometry and keeps Axis0/gravity/physics consumers blocked.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = !verdicts["controls_pass"] || result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["nested_readout"]
    f = result["flat_readout"]
    println("xi_shell_bridge_probe - Julia full sim")
    println("nested_hopf I_c=", n["I_c_A_to_B"], " S(A|B)=", n["S_A_given_B"], " I(A:B)=", n["I_A_B"])
    println("flat_s2_product I_c=", f["I_c_A_to_B"], " S(A|B)=", f["S_A_given_B"], " I(A:B)=", f["I_A_B"])
    println("xi_geometry_load_bearing=", result["xi_geometry_load_bearing"],
        " verdict=", result["geometry_load_bearing_verdict"],
        " nested_flat_delta_max=", result["nested_flat_delta"]["max"])
    println("scrambled_Omega_changes_readout=", result["controls"]["scrambled_Omega_changes_readout"],
        " delta_max=", result["scrambled_Omega_control"]["delta_from_nested"]["max"])
    println("one_future_degenerates=", result["one_future_control"]["degenerate"],
        " S_AB=", result["one_future_control"]["readout"]["S_AB"],
        " effective_rank=", result["one_future_control"]["readout"]["effective_rank"])
    println("product_no_entanglement_cut_Ic_zero=", result["controls"]["product_no_entanglement_cut_Ic_zero"],
        " I_c=", result["product_no_entanglement_cut"]["readout"]["I_c_A_to_B"])
    println("controllable_ftl_message_capacity=", result["ftl_message_capacity_check"]["controllable_ftl_message_capacity"],
        " branch_rho_A_linf_diff=", result["ftl_message_capacity_check"]["branch_rho_A_linf_diff"],
        " global_readout_delta_max=", result["ftl_message_capacity_check"]["global_readout_delta"]["max"])
    println("parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"])
    println("blocked_consumers=", join(result["blocked_consumers"], ","))
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    println("STOP: xi_shell_bridge_probe control/parity condition failed.")
    exit(2)
end
