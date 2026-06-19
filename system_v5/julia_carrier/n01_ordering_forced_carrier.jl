# n01_ordering_forced_carrier.jl
#
# object_id: n01_ordering_forced_carrier_v1
# claim_ceiling: Tests whether order-dependence is forced by N01 or merely chosen;
#   does NOT assert layer-completion, manifold admission, coupling, bridge, flux,
#   or physics.
# promotion_allowed: false
#
# Root gate only:
#   F01: finite-dimensional carrier/probe/operator/path set.
#   N01: there exists a non-commuting operator pair A,B with AB != BA.
#
# Finite map:
#   (dim, state_index, op_pair_type) ->
#     {order_gap, n01_witnessed, commutator_norm, order_forced}
#
# Domain:
#   dim in {2,3,4,6,8}
#   state_index in 1..16
#   op_pair_type in {n01_witnessing, commuting_control}
#
# Codomain:
#   order gap magnitude norm(A*B*psi - B*A*psi), N01 witness status,
#   commutator norm, and statewise order-forced bool.
#
# This is a bounded carrier/constraint diagnostic. It does not promote any
# downstream layer, bridge, flux, Axis0, basin, manifold, or physics consumer.

using LinearAlgebra
using Random
using Statistics

try
    @eval using JSON
catch first_error
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch second_error
        error("JSON package unavailable in global or local julia_carrier project: $(second_error)")
    end
end

const OBJECT_ID = "n01_ordering_forced_carrier_v1"
const CLAIM_CEILING = "Tests whether order-dependence is forced by N01 or merely chosen; does NOT assert layer-completion, manifold admission, coupling, bridge, flux, or physics."
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "n01_ordering_forced_carrier_results.json")
const RNG_SEED = 20260603
const TARGET_DIMS = [2, 3, 4, 6, 8]
const STATE_COUNT = 16
const ORDER_THRESHOLD = 1.0e-10
const CONTROL_THRESHOLD = 1.0e-12
const SIZE_LADDER_DIMS = [8, 16, 32, 64]
const SIZE_LADDER_STATES = 32

D(args...) = Dict{String,Any}(args...)

function random_state(rng::AbstractRNG, dim::Int)
    psi = randn(rng, dim) .+ 1im .* randn(rng, dim)
    nrm = norm(psi)
    if nrm <= eps(Float64)
        error("random_state produced a numerically zero vector at dim=$(dim)")
    end
    return ComplexF64.(psi ./ nrm)
end

function embedded_pauli_pair(dim::Int)
    if dim < 2
        error("embedded_pauli_pair requires dim >= 2")
    end
    sx = zeros(ComplexF64, dim, dim)
    sy = zeros(ComplexF64, dim, dim)
    sx[1, 2] = 1.0 + 0im
    sx[2, 1] = 1.0 + 0im
    sy[1, 2] = -1im
    sy[2, 1] = 1im
    return sx, sy
end

function commuting_diagonal_pair(dim::Int)
    d1 = ComplexF64.(collect(1:dim))
    d2 = ComplexF64.((collect(1:dim) .+ 1) .^ 2)
    return Matrix(Diagonal(d1)), Matrix(Diagonal(d2))
end

function gue_hermitian(rng::AbstractRNG, dim::Int)
    m = randn(rng, dim, dim) .+ 1im .* randn(rng, dim, dim)
    h = (m + m') / (2.0 * sqrt(float(dim)))
    return ComplexF64.(h)
end

function order_gap(A::AbstractMatrix, B::AbstractMatrix, psi::AbstractVector)
    # Match the requested finite-map readout exactly: norm(A*B*psi - B*A*psi).
    # Forming the products first keeps commuting diagonal controls exactly zero.
    deductive = (A * B) * psi
    inductive = (B * A) * psi
    return Float64(norm(deductive - inductive))
end

function commutator_norm(A::AbstractMatrix, B::AbstractMatrix)
    return Float64(norm(A * B - B * A))
end

function eigen_residual(A::AbstractMatrix, psi::AbstractVector)
    lambda = dot(psi, A * psi) / dot(psi, psi)
    return Float64(norm(A * psi - lambda * psi))
end

function summarize_gaps(rows)
    gaps = Float64[row["order_gap"] for row in rows]
    forced_flags = Bool[row["order_forced"] for row in rows]
    return D(
        "count" => length(gaps),
        "min_gap" => minimum(gaps),
        "max_gap" => maximum(gaps),
        "mean_gap" => mean(gaps),
        "median_gap" => median(gaps),
        "positive_count" => count(g -> g > ORDER_THRESHOLD, gaps),
        "zero_or_below_threshold_count" => count(g -> g <= ORDER_THRESHOLD, gaps),
        "all_order_forced" => all(forced_flags),
    )
end

function finite_map_entry(dim::Int, state_index::Int, op_pair_type::String, psi::Vector{ComplexF64})
    if op_pair_type == "n01_witnessing"
        A, B = embedded_pauli_pair(dim)
    elseif op_pair_type == "commuting_control"
        A, B = commuting_diagonal_pair(dim)
    else
        error("unknown op_pair_type=$(op_pair_type)")
    end

    cn = commutator_norm(A, B)
    gap = order_gap(A, B, psi)
    n01_witnessed = cn > ORDER_THRESHOLD
    generic_state = norm(psi) > CONTROL_THRESHOLD &&
        eigen_residual(A, psi) > ORDER_THRESHOLD &&
        eigen_residual(B, psi) > ORDER_THRESHOLD

    return D(
        "dim" => dim,
        "state_index" => state_index,
        "op_pair_type" => op_pair_type,
        "order_gap" => gap,
        "n01_witnessed" => n01_witnessed,
        "commutator_norm" => cn,
        "order_forced" => n01_witnessed && generic_state && gap > ORDER_THRESHOLD,
        "generic_state" => generic_state,
        "eigen_residual_A" => eigen_residual(A, psi),
        "eigen_residual_B" => eigen_residual(B, psi),
    )
end

function run_finite_map()
    rng = MersenneTwister(RNG_SEED)
    rows = Vector{Dict{String,Any}}()
    states_by_dim = D()

    for dim in TARGET_DIMS
        dim_states = Vector{Vector{ComplexF64}}()
        for state_index in 1:STATE_COUNT
            psi = random_state(rng, dim)
            push!(dim_states, psi)
            push!(rows, finite_map_entry(dim, state_index, "n01_witnessing", psi))
            push!(rows, finite_map_entry(dim, state_index, "commuting_control", psi))
        end
        states_by_dim["dim_$(dim)"] = dim_states
    end
    return rows, states_by_dim
end

function n01_existence_checks()
    checks = D()
    dim1_A = ComplexF64[2.0;;]
    dim1_B = ComplexF64[3.0;;]
    checks["dim_1_excluded"] = D(
        "dim" => 1,
        "F01_finite" => true,
        "commutator_norm" => commutator_norm(dim1_A, dim1_B),
        "n01_witnessed" => false,
        "admitted_under_F01_N01" => false,
        "reason" => "dim=1 finite carriers have only scalar 1x1 operators, so N01 is excluded.",
    )

    for dim in TARGET_DIMS
        A, B = embedded_pauli_pair(dim)
        cn = commutator_norm(A, B)
        checks["dim_$(dim)"] = D(
            "dim" => dim,
            "F01_finite" => true,
            "commutator_norm" => cn,
            "n01_witnessed" => cn > ORDER_THRESHOLD,
            "admitted_under_F01_N01" => cn > ORDER_THRESHOLD,
            "witness_pair" => "embedded sx, sy on a two-dimensional subspace",
        )
    end
    return checks
end

function boundary_checks()
    checks = D()
    for dim in TARGET_DIMS
        A, B = embedded_pauli_pair(dim)
        sx_plus = zeros(ComplexF64, dim)
        sx_plus[1] = inv(sqrt(2.0))
        sx_plus[2] = inv(sqrt(2.0))

        sy_plus = zeros(ComplexF64, dim)
        sy_plus[1] = inv(sqrt(2.0))
        sy_plus[2] = 1im * inv(sqrt(2.0))

        dim_checks = [
            D(
                "state" => "sx_plus_eigenstate",
                "eigen_residual_A" => eigen_residual(A, sx_plus),
                "eigen_residual_B" => eigen_residual(B, sx_plus),
                "order_gap" => order_gap(A, B, sx_plus),
                "below_order_threshold" => order_gap(A, B, sx_plus) <= ORDER_THRESHOLD,
                "note" => "Eigenstate of A only; for embedded Pauli this does not erase the commutator action.",
            ),
            D(
                "state" => "sy_plus_eigenstate",
                "eigen_residual_A" => eigen_residual(A, sy_plus),
                "eigen_residual_B" => eigen_residual(B, sy_plus),
                "order_gap" => order_gap(A, B, sy_plus),
                "below_order_threshold" => order_gap(A, B, sy_plus) <= ORDER_THRESHOLD,
                "note" => "Eigenstate of B only; for embedded Pauli this does not erase the commutator action.",
            ),
        ]

        if dim > 2
            common_kernel = zeros(ComplexF64, dim)
            common_kernel[3] = 1.0 + 0im
            push!(dim_checks, D(
                "state" => "embedded_common_kernel_basis_e3",
                "eigen_residual_A" => eigen_residual(A, common_kernel),
                "eigen_residual_B" => eigen_residual(B, common_kernel),
                "order_gap" => order_gap(A, B, common_kernel),
                "below_order_threshold" => order_gap(A, B, common_kernel) <= ORDER_THRESHOLD,
                "note" => "Shared zero-eigenstate created by embedding; this is a boundary state, not a generic random state.",
            ))
        end

        checks["dim_$(dim)"] = dim_checks
    end
    return checks
end

function size_ladder()
    rng = MersenneTwister(RNG_SEED + 99)
    ladder = D()
    for dim in SIZE_LADDER_DIMS
        A = gue_hermitian(rng, dim)
        B = gue_hermitian(rng, dim)
        cn = commutator_norm(A, B)
        gaps = Float64[]
        for _ in 1:SIZE_LADDER_STATES
            psi = random_state(rng, dim)
            push!(gaps, order_gap(A, B, psi))
        end
        ladder["dim_$(dim)"] = D(
            "dim" => dim,
            "pair_type" => "random_GUE_Hermitian_pair",
            "state_count" => SIZE_LADDER_STATES,
            "commutator_norm" => cn,
            "n01_witnessed" => cn > ORDER_THRESHOLD,
            "min_gap" => minimum(gaps),
            "max_gap" => maximum(gaps),
            "mean_gap" => mean(gaps),
            "median_gap" => median(gaps),
            "generic_nonzero_count" => count(g -> g > ORDER_THRESHOLD, gaps),
            "generic_nonzero_fraction" => count(g -> g > ORDER_THRESHOLD, gaps) / length(gaps),
            "pass" => cn > ORDER_THRESHOLD && all(g -> g > ORDER_THRESHOLD, gaps),
        )
    end
    return ladder
end

function wrong_structure_control(states_by_dim)
    control = D(
        "label" => "Uz_Ez_like_commuting_diagonal_control",
        "purpose" => "Shows the earlier ordering engine fails when its operator pair does not witness N01.",
        "per_dim" => D(),
    )

    for dim in TARGET_DIMS
        U_like, E_like = commuting_diagonal_pair(dim)
        gaps = Float64[]
        for psi in states_by_dim["dim_$(dim)"]
            push!(gaps, order_gap(U_like, E_like, psi))
        end
        control["per_dim"]["dim_$(dim)"] = D(
            "dim" => dim,
            "commutator_norm" => commutator_norm(U_like, E_like),
            "max_gap" => maximum(gaps),
            "all_gaps_under_control_threshold" => all(g -> g < CONTROL_THRESHOLD, gaps),
            "verdict" => "wrong_structure_control_passes_only_as_commuting_failure_case",
        )
    end
    return control
end

function summarize_by_dim_and_pair(rows)
    summary = D()
    for dim in TARGET_DIMS
        dim_summary = D()
        for pair_type in ["n01_witnessing", "commuting_control"]
            subset = [row for row in rows if row["dim"] == dim && row["op_pair_type"] == pair_type]
            dim_summary[pair_type] = summarize_gaps(subset)
            dim_summary[pair_type]["commutator_norm"] = subset[1]["commutator_norm"]
            dim_summary[pair_type]["n01_witnessed"] = subset[1]["n01_witnessed"]
        end
        summary["dim_$(dim)"] = dim_summary
    end
    return summary
end

function decide_verdict(summary, ladder, wrong_control)
    n01_dims_all_positive = all(
        summary["dim_$(dim)"]["n01_witnessing"]["all_order_forced"] for dim in TARGET_DIMS
    )
    commuting_dims_all_zero = all(
        summary["dim_$(dim)"]["commuting_control"]["max_gap"] < CONTROL_THRESHOLD for dim in TARGET_DIMS
    )
    wrong_structure_all_zero = all(
        wrong_control["per_dim"]["dim_$(dim)"]["all_gaps_under_control_threshold"] for dim in TARGET_DIMS
    )
    ladder_all_positive = all(ladder["dim_$(dim)"]["pass"] for dim in SIZE_LADDER_DIMS)
    dim2_positive = summary["dim_2"]["n01_witnessing"]["all_order_forced"]

    if !(commuting_dims_all_zero && wrong_structure_all_zero)
        return "open", "Commuting controls did not collapse; anti-fabrication control failed."
    elseif n01_dims_all_positive && ladder_all_positive
        return "forced_by_F01_N01",
            "N01 forces existence of a noncommuting witness pair, and using that witness makes generic random-state order gaps nonzero across admitted finite carriers and the GUE size ladder."
    elseif dim2_positive && !n01_dims_all_positive
        return "forced_by_F01_N01_plus_minimality",
            "The nonzero generic order gap held only under the minimal dim=2 carrier choice."
    elseif any(summary["dim_$(dim)"]["n01_witnessing"]["zero_or_below_threshold_count"] > 0 for dim in TARGET_DIMS)
        return "chosen_principle",
            "At least one generic random state had a zero/below-threshold gap despite an N01 witness."
    else
        return "open", "The finite checks did not cleanly decide forced vs chosen."
    end
end

function build_result()
    finite_rows, states_by_dim = run_finite_map()
    summary = summarize_by_dim_and_pair(finite_rows)
    n01_checks = n01_existence_checks()
    boundary = boundary_checks()
    ladder = size_ladder()
    wrong_control = wrong_structure_control(states_by_dim)
    verdict, verdict_reason = decide_verdict(summary, ladder, wrong_control)

    boundary_zero_states = D()
    for dim in TARGET_DIMS
        zero_rows = [row for row in boundary["dim_$(dim)"] if row["below_order_threshold"]]
        boundary_zero_states["dim_$(dim)"] = zero_rows
    end

    anti_fabrication = D(
        "commuting_pair_control_required_zero" => true,
        "commuting_pair_control_pass" => all(
            summary["dim_$(dim)"]["commuting_control"]["max_gap"] < CONTROL_THRESHOLD for dim in TARGET_DIMS
        ),
        "wrong_structure_control_pass" => all(
            wrong_control["per_dim"]["dim_$(dim)"]["all_gaps_under_control_threshold"] for dim in TARGET_DIMS
        ),
        "n01_witness_random_generic_required_nonzero" => true,
        "n01_witness_random_generic_pass" => all(
            summary["dim_$(dim)"]["n01_witnessing"]["all_order_forced"] for dim in TARGET_DIMS
        ),
        "verdict_flips_if_n01_random_gaps_zero" => true,
    )

    return D(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "classification" => "constraint_probe",
        "promotion_status" => "diagnostic_only",
        "root_constraints_in_force" => [
            "F01 finite-dimensional H,P,O,Gamma / finite carrier-probe-operator-path set",
            "N01 exists A,B such that AB != BA",
        ],
        "finite_map_definition" => D(
            "map" => "(dim, state_index, op_pair_type) -> {order_gap, n01_witnessed, commutator_norm, order_forced}",
            "domain" => D(
                "dim" => TARGET_DIMS,
                "state_index" => "1..$(STATE_COUNT), fixed seed random normalized complex states",
                "op_pair_type" => ["n01_witnessing", "commuting_control"],
            ),
            "codomain_or_output" => D(
                "order_gap" => "Float64 norm(A*B*psi - B*A*psi)",
                "n01_witnessed" => "Bool commutator_norm > $(ORDER_THRESHOLD)",
                "commutator_norm" => "Float64 norm(A*B - B*A)",
                "order_forced" => "Bool n01_witnessed && generic_state && order_gap > $(ORDER_THRESHOLD)",
            ),
        ),
        "parameters" => D(
            "rng_seed" => RNG_SEED,
            "order_threshold" => ORDER_THRESHOLD,
            "control_threshold" => CONTROL_THRESHOLD,
            "target_dims" => TARGET_DIMS,
            "states_per_dim" => STATE_COUNT,
            "size_ladder_dims" => SIZE_LADDER_DIMS,
            "size_ladder_states_per_dim" => SIZE_LADDER_STATES,
        ),
        "finite_map" => finite_rows,
        "summary_by_dim_and_pair" => summary,
        "n01_existence_checks" => n01_checks,
        "positive_checks" => D(
            "n01_witnessing_pairs" => D(
                "expected" => "generic random states show order_gap > threshold",
                "pass" => all(summary["dim_$(dim)"]["n01_witnessing"]["all_order_forced"] for dim in TARGET_DIMS),
                "per_dim" => D("dim_$(dim)" => summary["dim_$(dim)"]["n01_witnessing"] for dim in TARGET_DIMS),
            ),
        ),
        "negative_controls" => D(
            "commuting_control_pairs" => D(
                "expected" => "order_gap < control_threshold for every random state because [A,B]=0",
                "pass" => all(summary["dim_$(dim)"]["commuting_control"]["max_gap"] < CONTROL_THRESHOLD for dim in TARGET_DIMS),
                "per_dim" => D("dim_$(dim)" => summary["dim_$(dim)"]["commuting_control"] for dim in TARGET_DIMS),
            ),
            "uz_ez_wrong_structure_control" => wrong_control,
        ),
        "boundary_checks" => D(
            "checks" => boundary,
            "zero_or_below_threshold_boundary_states" => boundary_zero_states,
            "interpretation" => "A nonzero commutator forces an order-sensitive engine, not a universal positive gap on every possible state. Boundary/kernel states can erase the readout; random generic states did not.",
        ),
        "size_ladder" => ladder,
        "tool_manifest" => D(
            "LinearAlgebra" => "load-bearing matrix products, commutator norms, vector norms, diagonal embeddings",
            "Random" => "load-bearing fixed-seed random state and GUE Hermitian pair generation",
            "Statistics" => "supportive gap summaries: mean and median",
            "JSON" => "artifact emission to canonical result JSON path",
        ),
        "TOOL_MANIFEST" => D(
            "LinearAlgebra" => "load-bearing matrix products, commutator norms, vector norms, diagonal embeddings",
            "Random" => "load-bearing fixed-seed random state and GUE Hermitian pair generation",
            "Statistics" => "supportive gap summaries: mean and median",
            "JSON" => "artifact emission to canonical result JSON path",
        ),
        "tool_integration_depth" => D(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => D(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
        ),
        "allowed_claims" => [
            "N01 excludes dim=1 and supplies a noncommuting witness pair for finite carriers with dim >= 2.",
            "For engines built on the N01-witnessing pair, generic random states show nonzero order gap.",
            "Commuting pairs like the Uz/Ez analogy are wrong-structure controls and show zero order gap.",
        ],
        "blocked_consumers" => [
            "layer_completion",
            "manifold_admission",
            "coupling",
            "bridge",
            "flux",
            "Axis0",
            "basin",
            "physics",
        ],
        "eligible_consumers" => [
            "bounded F01+N01 ordering rescue audit",
            "future lower-tier carrier/probe comparison with the same no-promotion ceiling",
        ],
        "anti_fabrication" => anti_fabrication,
        "verdict" => verdict,
        "forced_or_chosen" => verdict,
        "verdict_reason" => verdict_reason,
        "honest_caveat" => "Order gap is nonzero for generic random states when the engine uses an N01-witnessing pair. It is not a state-universal claim: boundary/kernel states can have zero gap, and commuting pairs like Uz/Ez fail because they do not witness N01.",
        "strict_statewise_universal_order_gap" => "not_forced",
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end

    println("object_id: $(OBJECT_ID)")
    println("result_json: $(RESULT_PATH)")
    println("VERDICT: $(result["verdict"])")

    if !(result["anti_fabrication"]["commuting_pair_control_pass"] &&
          result["anti_fabrication"]["wrong_structure_control_pass"] &&
          result["anti_fabrication"]["n01_witness_random_generic_pass"])
        error("anti-fabrication checks failed; see $(RESULT_PATH)")
    end
end

main()
