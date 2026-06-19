#!/usr/bin/env julia
# object_id: weyl_sheet_pair_probe
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "weyl_sheet_pair_probe"
const RESULT_PATH = joinpath(@__DIR__, "weyl_sheet_pair_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "weyl_sheet_pair_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const N_REF = Float64[0.0, 0.0, 1.0]

dm(psi::Vector{ComplexF64}) = psi * psi'

function rho_from_bloch(r::Vector{Float64})
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY .+ r[3] .* SZ)
end

function bloch_from_rho(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function spinor_from_angles(theta::Float64, phi::Float64, fiber_phase::Float64)
    exp(im * fiber_phase) .* ComplexF64[
        cos(theta / 2.0),
        exp(im * phi) * sin(theta / 2.0),
    ]
end

function spinor_from_bloch(r::Vector{Float64}, fiber_phase::Float64)
    rn = r ./ norm(r)
    x, y, z = rn
    if 1.0 + z > 1.0e-12
        denom = sqrt(2.0 * (1.0 + z))
        section = ComplexF64[
            sqrt((1.0 + z) / 2.0),
            ComplexF64(x, y) / denom,
        ]
    else
        denom = sqrt(2.0 * (1.0 - z))
        section = ComplexF64[
            ComplexF64(x, -y) / denom,
            sqrt((1.0 - z) / 2.0),
        ]
    end
    exp(im * fiber_phase) .* (section ./ norm(section))
end

function canonical_section(r::Vector{Float64})
    spinor_from_bloch(r, 0.0)
end

function fiber_phase(psi::Vector{ComplexF64}, r::Vector{Float64})
    anchor = canonical_section(r)
    z = dot(anchor, psi)
    atan(imag(z), real(z))
end

wrap_phase(x::Float64) = atan(sin(x), cos(x))

function cross3(a::Vector{Float64}, b::Vector{Float64})
    Float64[
        a[2] * b[3] - a[3] * b[2],
        a[3] * b[1] - a[1] * b[3],
        a[1] * b[2] - a[2] * b[1],
    ]
end

function sigma_from_ref(n::Vector{Float64})
    n[1] .* SX .+ n[2] .* SY .+ n[3] .* SZ
end

function bool_scalar(x::Bool)
    x ? 1.0 : 0.0
end

function vec_payload(v::Vector{Float64})
    [Float64(x) for x in v]
end

function pair_metrics(label::String, psi_l::Vector{ComplexF64}, psi_r::Vector{ComplexF64})
    rho_l = dm(psi_l)
    rho_r = dm(psi_r)
    r_l = bloch_from_rho(rho_l)
    r_r = bloch_from_rho(rho_r)
    m_sigma = sigma_from_ref(N_REF)

    signed_volume = dot(cross3(r_l, r_r), N_REF)
    trace_chi = 2.0 * imag(tr(rho_l * rho_r * m_sigma))
    transverse_l = r_l .- dot(r_l, N_REF) .* N_REF
    transverse_r = r_r .- dot(r_r, N_REF) .* N_REF
    alpha_l = fiber_phase(psi_l, r_l)
    alpha_r = fiber_phase(psi_r, r_r)

    norm_residual = max(
        abs(real(dot(psi_l, psi_l)) - 1.0),
        abs(real(dot(psi_r, psi_r)) - 1.0),
    )
    trace_residual = max(
        abs(real(tr(rho_l)) - 1.0),
        abs(real(tr(rho_r)) - 1.0),
    )
    hermitian_residual = max(norm(rho_l - rho_l'), norm(rho_r - rho_r'))
    idempotency_residual = max(norm(rho_l * rho_l - rho_l), norm(rho_r * rho_r - rho_r))
    hopf_s2_residual = max(abs(norm(r_l) - 1.0), abs(norm(r_r) - 1.0))
    rho_rebuild_residual = max(
        norm(rho_l - rho_from_bloch(r_l)),
        norm(rho_r - rho_from_bloch(r_r)),
    )

    Dict{String,Any}(
        "label" => label,
        "chi" => Float64(signed_volume),
        "chi_trace_form" => Float64(trace_chi),
        "chi_trace_residual" => Float64(abs(signed_volume - trace_chi)),
        "r_L" => vec_payload(r_l),
        "r_R" => vec_payload(r_r),
        "rho_L_trace_residual" => Float64(abs(real(tr(rho_l)) - 1.0)),
        "rho_R_trace_residual" => Float64(abs(real(tr(rho_r)) - 1.0)),
        "spinor_norm_residual" => Float64(norm_residual),
        "trace_rho_residual" => Float64(trace_residual),
        "hermitian_residual" => Float64(hermitian_residual),
        "idempotency_residual" => Float64(idempotency_residual),
        "hopf_s2_residual" => Float64(hopf_s2_residual),
        "rho_reconstruction_residual" => Float64(rho_rebuild_residual),
        "relative_fiber_phase" => Float64(wrap_phase(alpha_l - alpha_r)),
        "fiber_phase_L" => Float64(alpha_l),
        "fiber_phase_R" => Float64(alpha_r),
        "transverse_scale" => Float64(norm(transverse_l) * norm(transverse_r)),
        "overlap_abs" => Float64(abs(dot(psi_l, psi_r))),
    )
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => true,
            "missing_from_peer" => collect(keys(result["shared_scalars"])),
            "missing_from_self" => String[],
            "stop_condition_fired" => true,
        )
    end

    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(setdiff(collect(keys(self_scalars)), collect(keys(peer_scalars))))
    missing_from_self = sort(setdiff(collect(keys(peer_scalars)), collect(keys(self_scalars))))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""

    for (key, value) in self_scalars
        if haskey(peer_scalars, key)
            diff = abs(Float64(value) - Float64(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end

    within = isempty(missing_from_peer) && isempty(missing_from_self) && max_diff < TOL
    strict_divergence = max_diff > STRICT_STOP_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => within,
        "strict_divergence_gt_1e_6" => strict_divergence,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
        "stop_condition_fired" => !within,
    )
end

function main()
    psi_l = spinor_from_angles(1.07, -0.41, 0.73)
    psi_r = spinor_from_angles(0.82, 1.26, -0.18)
    generic = pair_metrics("generic_independent_LR", psi_l, psi_r)
    swap = pair_metrics("swap_RL", psi_r, psi_l)
    no_chirality = pair_metrics("no_chirality_same_hopf_base_pure_phase", psi_l, exp(im * 0.61) .* psi_l)

    parity_base = bloch_from_rho(dm(spinor_from_angles(1.11, 0.37, 0.21)))
    reflected = parity_base .- 2.0 .* dot(parity_base, N_REF) .* N_REF
    parity_sym = pair_metrics(
        "parity_symmetric_reflection_across_ref_plane",
        spinor_from_bloch(parity_base, 0.22),
        spinor_from_bloch(reflected, -0.49),
    )

    no_chirality_antipodal = pair_metrics(
        "no_chirality_antipodal_hopf_base",
        spinor_from_bloch(parity_base, 0.14),
        spinor_from_bloch(-1.0 .* parity_base, -0.32),
    )

    sign_flip_residual = abs(Float64(generic["chi"]) + Float64(swap["chi"]))
    no_chirality_abs = abs(Float64(no_chirality["chi"]))
    parity_symmetric_abs = abs(Float64(parity_sym["chi"]))
    antipodal_abs = abs(Float64(no_chirality_antipodal["chi"]))

    controls = Dict{String,Any}(
        "swap_sign_flip" => sign_flip_residual <= TOL && Float64(generic["chi"]) * Float64(swap["chi"]) < 0.0,
        "no_chirality_zero" => no_chirality_abs <= TOL,
        "parity_symmetric_zero" => parity_symmetric_abs <= TOL,
        "no_chirality_antipodal_zero" => antipodal_abs <= TOL,
    )
    verdicts = Dict{String,Any}(
        "generic_independent_LR" => Float64(generic["overlap_abs"]) < 1.0 - 1.0e-6,
        "generic_chi_nonzero" => abs(Float64(generic["chi"])) > TOL,
        "chirality_load_bearing" => abs(Float64(generic["chi"])) > TOL &&
            (controls["swap_sign_flip"]::Bool) &&
            (controls["no_chirality_zero"]::Bool) &&
            (controls["parity_symmetric_zero"]::Bool),
        "controls_all_pass" => all(Bool(v) for v in values(controls)),
    )

    max_pair_residual = maximum(Float64[
        generic["chi_trace_residual"], generic["spinor_norm_residual"], generic["trace_rho_residual"],
        generic["hermitian_residual"], generic["idempotency_residual"], generic["hopf_s2_residual"],
        generic["rho_reconstruction_residual"], swap["chi_trace_residual"], no_chirality["chi_trace_residual"],
        parity_sym["chi_trace_residual"],
    ])

    shared_scalars = Dict{String,Any}(
        "generic_chi" => Float64(generic["chi"]),
        "generic_chi_trace_form" => Float64(generic["chi_trace_form"]),
        "generic_chi_trace_residual" => Float64(generic["chi_trace_residual"]),
        "generic_transverse_scale" => Float64(generic["transverse_scale"]),
        "generic_relative_fiber_phase" => Float64(generic["relative_fiber_phase"]),
        "generic_overlap_abs" => Float64(generic["overlap_abs"]),
        "swap_chi" => Float64(swap["chi"]),
        "swap_sign_flip_residual" => Float64(sign_flip_residual),
        "no_chirality_chi" => Float64(no_chirality["chi"]),
        "no_chirality_abs" => Float64(no_chirality_abs),
        "parity_symmetric_chi" => Float64(parity_sym["chi"]),
        "parity_symmetric_abs" => Float64(parity_symmetric_abs),
        "no_chirality_antipodal_chi" => Float64(no_chirality_antipodal["chi"]),
        "no_chirality_antipodal_abs" => Float64(antipodal_abs),
        "max_pair_residual" => Float64(max_pair_residual),
        "control_swap_sign_flip" => bool_scalar(controls["swap_sign_flip"]::Bool),
        "control_no_chirality_zero" => bool_scalar(controls["no_chirality_zero"]::Bool),
        "control_parity_symmetric_zero" => bool_scalar(controls["parity_symmetric_zero"]::Bool),
        "verdict_generic_chi_nonzero" => bool_scalar(verdicts["generic_chi_nonzero"]::Bool),
        "verdict_chirality_load_bearing" => bool_scalar(verdicts["chirality_load_bearing"]::Bool),
        "numpy_compute_used_flag" => 0.0,
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "backend_roles" => Dict(
            "julia" => "reference_exact_linearalgebra",
            "jax" => "mirror_stress_jnp_x64",
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "PROMOTION_ALLOWED" => false,
        "FORMAL_ADMISSION_ALLOWED" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "carrier_probe",
        "carrier_layer" => "left_right_weyl_pair_over_two_independent_hopf_maps",
        "geometry_layer" => "C2_spinor_to_Bloch_Hopf_base_per_sheet",
        "claim_ceiling" => "Carrier-only L/R Weyl sheet chirality diagnostic; no engine admission, Axis0, gravity, win/lose, bridge, or formal admission claim.",
        "allowed_claims" => [
            "finite chiral carrier readout for independent L/R Hopf-base sheets",
            "control-bounded load-bearing status of the parity-odd pair witness",
        ],
        "eligible_consumers" => ["formal_scout_review_only"],
        "blocked_consumers" => [
            "engine_admission",
            "Axis0",
            "gravity",
            "win_lose_dynamics",
            "formal_admission",
            "bridge_or_downstream_claim",
        ],
        "out_of_scope" => [
            "engine admission",
            "Axis0",
            "gravity",
            "win/lose dynamics",
            "formal admission",
            "bridge or downstream physical claim",
        ],
        "demotion_condition" => "Demote to miswired scratch diagnostic if swap sign does not flip, same-sheet phase control is nonzero, parity-symmetric reflection is nonzero, NumPy compute appears, or peer shared scalar parity fails.",
        "promotion_condition" => "None in this run; promotion_allowed is false and formal_admission_allowed is false.",
        "blocked_until" => "A separate admitted process defines IGT win/lose and downstream engine/Axis gates; this probe intentionally does not.",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "reference_axis" => Dict(
            "name" => "pauli_z_sheet_normal",
            "vector" => vec_payload(N_REF),
            "role" => "fixed label-neutral carrier-frame axis for the parity-odd witness",
        ),
        "witness" => Dict(
            "formula" => "chi = n_ref dot (r_L cross r_R)",
            "trace_equivalent" => "chi = 2 Im Tr(rho_L rho_R (n_ref dot sigma))",
            "swap_rule" => "chi(R,L) = -chi(L,R)",
            "fiber_phase_role" => "diagnostic_only_not_load_bearing",
        ),
        "tools" => ["Julia LinearAlgebra", "JAX jax.numpy x64"],
        "tool_manifest" => Dict(
            "Julia LinearAlgebra" => Dict(
                "tried" => true,
                "used" => true,
                "role" => "reference_exact_linearalgebra",
                "reason" => "load-bearing for density matrices, Pauli traces, Bloch vectors, cross/dot witness, and residual norms",
            ),
            "JAX jax.numpy x64" => Dict(
                "tried" => true,
                "used" => false,
                "role" => "peer_mirror_expected",
                "reason" => "supportive peer parity lane read from its result JSON when present; no JAX compute is used inside Julia",
            ),
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => Dict(
                "tried" => true,
                "used" => true,
                "role" => "reference_exact_linearalgebra",
                "reason" => "load-bearing for density matrices, Pauli traces, Bloch vectors, cross/dot witness, and residual norms",
            ),
            "JAX jax.numpy x64" => Dict(
                "tried" => true,
                "used" => false,
                "role" => "peer_mirror_expected",
                "reason" => "supportive peer parity lane read from its result JSON when present; no JAX compute is used inside Julia",
            ),
        ),
        "tool_integration_depth" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "JAX jax.numpy x64" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "JAX jax.numpy x64" => "supportive",
        ),
        "numpy_compute_used" => false,
        "jax_x64_enabled" => nothing,
        "pairs" => Dict(
            "generic" => generic,
            "swap" => swap,
            "no_chirality" => no_chirality,
            "parity_symmetric" => parity_sym,
            "no_chirality_antipodal" => no_chirality_antipodal,
        ),
        "controls" => controls,
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "divergence_log" => [
            "Generic independent L/R sheets produce nonzero chi under the fixed carrier-frame reference axis.",
            "L/R swap is required to flip chi sign, not merely change magnitude.",
            "Same Hopf base with pure fiber phase and parity-symmetric reflected base are required to collapse chi to zero.",
            "This divergence is carrier-only and does not define IGT win/lose, engine admission, Axis0, gravity, bridge, or formal admission.",
        ],
        "honest_caveat" => "scratch_diagnostic is used intentionally; generic receipt validators that only admit canonical/classical/tool-fit/supporting/audit classes may reject this as noncanonical.",
        "plain_sentence" => "L/R chirality is load-bearing for this finite chiral carrier witness: the independent sheet pair has a nonzero parity-odd readout, while same-sheet and parity-symmetric controls collapse to generic spinor geometry.",
    )
    result["parity"] = parity_block(result)
    result["all_pass"] = !(result["numpy_compute_used"]::Bool) &&
        (verdicts["generic_independent_LR"]::Bool) &&
        (verdicts["chirality_load_bearing"]::Bool) &&
        (verdicts["controls_all_pass"]::Bool) &&
        (result["parity"]["within_1e_9"]::Bool)
    result["stop_condition_fired"] = !(result["all_pass"]::Bool)

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("weyl_sheet_pair_probe julia wrote $(RESULT_PATH)")
    println("generic_chi=$(generic["chi"]) swap_chi=$(swap["chi"]) no_chirality_chi=$(no_chirality["chi"]) parity_symmetric_chi=$(parity_sym["chi"])")
    println("chirality_load_bearing=$(verdicts["chirality_load_bearing"]) parity_max_diff=$(result["parity"]["parity_max_diff"])")
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED weyl_sheet_pair_probe julia")
        exit(1)
    end
end

main()
