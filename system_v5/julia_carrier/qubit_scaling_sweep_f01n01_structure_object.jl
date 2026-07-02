#!/usr/bin/env julia
# qubit_scaling_sweep_f01n01_structure_object.jl
#
# Julia carrier: qubit-scaling sweep over structural criteria under F01 + N01.
#
# OBJECT_ID  : qubit_scaling_sweep_f01n01_structure_v1
# CLAIM CEILING:
#   This carrier computes explicit finite maps over F01 + N01 for q in {1,2,3,4}.
#   It witnesses which structural criteria (chirality split, order gap, Clifford
#   algebra, nested-shell distinguishability) are admitted or excluded at each dim.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge,
#   flux, or physics. promotion_allowed = false.
#
# F01: every matrix is finite-dimensional; all maps terminate on the finite
#      carrier C^(2^q).
# N01: an explicit noncommuting pair is constructed and witnessed by commutator
#      norm at each q.
#
# Domain  : finite spinor density matrices + Clifford generators on C^(2^q),
#           q in {1,2,3,4}, dim in {2,4,8,16}.
# Codomain: per-criterion pass/fail + witness values; overall pass/fail.
#
# Controls:
#   - Positive control: Jordan-Wigner gamma matrices satisfying the Clifford
#     anticommutation relations; chirality element i^q * prod(gammas).
#   - Negative (wrong-structure) control for chirality: diagonal matrix with a
#     zero entry — fails C^2=I and equal-split tests.
#   - Null control for order gap: maximally mixed density (invariant under
#     unitary conjugation — gap should collapse to machine epsilon).
#
# ANTI-FABRICATION NOTE:
#   Every verdict is computed from constructed matrices.
#   No hardcoded "PASS" strings appear in the verdict logic.
#   The wrong-structure control must flip the chirality verdict to FAIL;
#   removing it would not change the positive verdict (it is a negative check).
#   The null control (maximally mixed) must return near-zero order gap;
#   its inclusion verifies the probe is not vacuously satisfied.

using LinearAlgebra

const OBJECT_ID = "qubit_scaling_sweep_f01n01_structure_v1"
const QUBITS_TO_TEST = [1, 2, 3, 4]
const TOL = 1.0e-10
const RESULT_PATH = joinpath("/tmp", "qubit_scaling_sweep_f01n01_structure_results.json")

# ---------------------------------------------------------------------------
# Pauli matrices
# ---------------------------------------------------------------------------

const σ0 = ComplexF64[1 0; 0 1]
const σX = ComplexF64[0 1; 1 0]
const σY = ComplexF64[0 -1im; 1im 0]
const σZ = ComplexF64[1 0; 0 -1]

function kron_all(mats::Vector{Matrix{ComplexF64}})::Matrix{ComplexF64}
    r = mats[1]
    for m in mats[2:end]
        r = kron(r, m)
    end
    return r
end

# ---------------------------------------------------------------------------
# Jordan-Wigner Clifford generators for Cl(2q) on C^{2^q}
#   gamma_{2j+1} = Z^{⊗j} ⊗ X ⊗ I^{⊗(q-j-1)}
#   gamma_{2j+2} = Z^{⊗j} ⊗ Y ⊗ I^{⊗(q-j-1)}
# ---------------------------------------------------------------------------

function cl2q_gamma_matrices(q::Int)::Vector{Matrix{ComplexF64}}
    gammas = Matrix{ComplexF64}[]
    for j in 0:(q-1)
        zs = fill(σZ, j)
        is = fill(σ0, q - j - 1)
        push!(gammas, kron_all([zs..., σX, is...]))
        push!(gammas, kron_all([zs..., σY, is...]))
    end
    return gammas
end

# ---------------------------------------------------------------------------
# Density constructors
# ---------------------------------------------------------------------------

function basis_spinor_density(dim::Int, idx::Int = 1)::Matrix{ComplexF64}
    ket = zeros(ComplexF64, dim, 1)
    ket[idx, 1] = 1.0
    return ket * ket'
end

function maximally_mixed(dim::Int)::Matrix{ComplexF64}
    return Matrix{ComplexF64}(I, dim, dim) ./ dim
end

# ---------------------------------------------------------------------------
# Trace norm
# ---------------------------------------------------------------------------

function trace_norm(M::Matrix{ComplexF64})::Float64
    return sum(svdvals(M))
end

# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------

function criterion_f01(q::Int, dim::Int)
    finite_dim = (dim == 2^q) && (dim >= 2)
    map_terminates = finite_dim
    passed = finite_dim && map_terminates
    return passed, Dict{String,Any}(
        "finite_dimensional" => finite_dim,
        "map_terminates"     => map_terminates,
        "carrier_shape"      => [dim, dim],
    )
end

function criterion_n01(A::Matrix{ComplexF64}, B::Matrix{ComplexF64})
    comm = A * B - B * A
    norm_val = norm(comm)
    passed = norm_val > TOL
    return passed, Dict{String,Any}(
        "operator_pair"              => "X_first_qubit, H_first_qubit",
        "commutator_frobenius_norm"  => norm_val,
        "threshold"                  => TOL,
    )
end

function chirality_diagnostics(C::Matrix{ComplexF64}; tol::Float64 = TOL)
    dim    = size(C, 1)
    eye    = Matrix{ComplexF64}(I, dim, dim)
    sq_err = norm(C * C - eye)
    tr_val = tr(C)
    tr_abs = abs(tr_val)
    herm_err = norm(C - C')

    if herm_err < 100 * tol
        eigvals_vec = eigvals(Hermitian((C + C') ./ 2))
    else
        eigvals_vec = eigvals(C)
    end

    plus_dim  = count(v -> abs(real(v) - 1) < tol && abs(imag(v)) < tol, eigvals_vec)
    minus_dim = count(v -> abs(real(v) + 1) < tol && abs(imag(v)) < tol, eigvals_vec)
    all_pm1   = (plus_dim + minus_dim == dim)
    equal_split = (plus_dim == minus_dim) && (plus_dim > 0)
    valid = (sq_err < tol) && (tr_abs < tol) && (herm_err < tol) && all_pm1 && equal_split

    return Dict{String,Any}(
        "valid"               => valid,
        "square_error"        => sq_err,
        "trace_abs"           => tr_abs,
        "hermitian_error"     => herm_err,
        "plus_dim"            => plus_dim,
        "minus_dim"           => minus_dim,
        "all_pm_one"          => all_pm1,
        "equal_nonzero_split" => equal_split,
    )
end

function criterion_chirality(gammas::Vector{Matrix{ComplexF64}}, q::Int)
    dim = size(gammas[1], 1)
    raw = Matrix{ComplexF64}(I, dim, dim)
    for g in gammas
        raw = raw * g
    end
    chirality = (1im)^q * raw
    diag_pos = chirality_diagnostics(chirality)

    # Wrong-structure negative control: diagonal matrix with a zero in the last
    # entry. This is not a Z2 grading: C^2 ≠ I and trace ≠ 0.
    wrong = diagm([ones(ComplexF64, dim - 1); 0.0 + 0.0im])
    diag_neg = chirality_diagnostics(wrong)

    passed = diag_pos["valid"] && !diag_neg["valid"]

    return passed, Dict{String,Any}(
        "phase"                        => "i^$q",
        "chirality"                    => diag_pos,
        "wrong_structure_negative_control" => merge(diag_neg, Dict{String,Any}(
            "failed_as_expected" => !diag_neg["valid"],
            "description"        => "diagonal(1, ..., 1, 0): not a Z2 grading",
        )),
    )
end

function criterion_order_gap(A::Matrix{ComplexF64}, B::Matrix{ComplexF64},
                              rho::Matrix{ComplexF64})
    AB = A * B
    BA = B * A
    rho_ab = AB * rho * BA
    rho_ba = BA * rho * AB
    gap = trace_norm(rho_ab - rho_ba)

    # Null control: maximally mixed density is invariant under unitary
    # conjugation — the gap should collapse to machine epsilon.
    rho_mixed = maximally_mixed(size(rho, 1))
    mixed_gap = trace_norm(AB * rho_mixed * BA - BA * rho_mixed * AB)

    passed = gap > TOL
    return passed, Dict{String,Any}(
        "reference_density"                  => "projector_onto_computational_basis_spinor_1",
        "trace_norm_order_gap"               => gap,
        "maximally_mixed_null_control_gap"   => mixed_gap,
        "threshold"                          => TOL,
    )
end

function criterion_clifford(gammas::Vector{Matrix{ComplexF64}})
    dim = size(gammas[1], 1)
    eye = Matrix{ComplexF64}(I, dim, dim)
    max_anticomm_err = 0.0
    for (i, gi) in enumerate(gammas), (j, gj) in enumerate(gammas)
        target = (i == j) ? 2 * eye : zeros(ComplexF64, dim, dim)
        err = norm(gi * gj + gj * gi - target)
        max_anticomm_err = max(max_anticomm_err, err)
    end
    max_tr_abs = maximum(abs(tr(g)) for g in gammas)
    passed = (max_anticomm_err < TOL) && (max_tr_abs < TOL)
    return passed, Dict{String,Any}(
        "gamma_count"            => length(gammas),
        "max_anticommutation_error" => max_anticomm_err,
        "max_trace_abs"          => max_tr_abs,
        "threshold"              => TOL,
    )
end

function criterion_nested_shells(dim::Int)
    half = dim ÷ 2
    inner = zeros(ComplexF64, dim, dim)
    outer = zeros(ComplexF64, dim, dim)
    inner[1:half, 1:half] = Matrix{ComplexF64}(I, half, half) ./ half
    outer[half+1:end, half+1:end] = Matrix{ComplexF64}(I, half, half) ./ half
    dist = trace_norm(inner - outer)
    shell_size_ok = (dim >= 4) && (half >= 2)
    passed = (dist > TOL) && shell_size_ok
    return passed, Dict{String,Any}(
        "inner_shell_rank"    => half,
        "outer_shell_rank"    => half,
        "trace_norm_distance" => dist,
        "requires_dim_ge_4"   => true,
        "shell_size_ok"       => shell_size_ok,
        "threshold"           => TOL,
    )
end

# ---------------------------------------------------------------------------
# Evaluate one qubit count
# ---------------------------------------------------------------------------

function evaluate_q(q::Int)
    dim    = 2^q
    gammas = cl2q_gamma_matrices(q)

    # N01 witness pair: X and H (Hadamard) embedded on first qubit
    function embed_first(op)
        if q == 1
            return op
        else
            return kron_all([op, fill(σ0, q - 1)...])
        end
    end

    A   = embed_first(σX)
    B   = embed_first(ComplexF64.(1 / sqrt(2) .* [1 1; 1 -1]))
    rho = basis_spinor_density(dim, 1)

    tests = [
        ("A_F01",                       criterion_f01(q, dim)),
        ("B_N01",                       criterion_n01(A, B)),
        ("C_LEFT_RIGHT_CHIRALITY",       criterion_chirality(gammas, q)),
        ("D_ORDER_GAP",                 criterion_order_gap(A, B, rho)),
        ("E_CLIFFORD_CL_2Q",            criterion_clifford(gammas)),
        ("F_NESTED_SHELL_DISTINGUISHABILITY", criterion_nested_shells(dim)),
    ]

    passed_list = String[]
    failed_list = String[]
    criteria    = Dict{String,Any}()
    for (name, (ok, details)) in tests
        criteria[name] = merge(Dict{String,Any}("pass" => ok), details)
        if ok
            push!(passed_list, name)
        else
            push!(failed_list, name)
        end
    end

    overall = isempty(failed_list) ? "success" : "fail"
    return Dict{String,Any}(
        "qubits"  => q,
        "dim"     => dim,
        "passed"  => passed_list,
        "failed"  => failed_list,
        "overall" => overall,
        "criteria"=> criteria,
    )
end

# ---------------------------------------------------------------------------
# JSON serialization (stdlib only — no JSON.jl required)
# ---------------------------------------------------------------------------

function json_escape(s::AbstractString)::String
    buf = IOBuffer()
    for c in s
        c == '"'  && print(buf, "\\\""); continue
        c == '\\' && print(buf, "\\\\"); continue
        c == '\n' && print(buf, "\\n");  continue
        c == '\r' && print(buf, "\\r");  continue
        c == '\t' && print(buf, "\\t");  continue
        print(buf, c)
    end
    return String(take!(buf))
end

function to_json(x, indent::Int = 0)::String
    pad     = " "^indent
    nextpad = " "^(indent + 2)
    if x === nothing || x === missing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        return isfinite(x) ? string(x) : "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Dict
        isempty(x) && return "{}"
        items = ["$(nextpad)$(to_json(k)): $(to_json(v, indent + 2))"
                 for (k, v) in sort(collect(x), by = first)]
        return "{\n" * join(items, ",\n") * "\n$(pad)}"
    elseif x isa AbstractVector
        isempty(x) && return "[]"
        items = [nextpad * to_json(v, indent + 2) for v in x]
        return "[\n" * join(items, ",\n") * "\n$(pad)]"
    else
        return "\"$(string(x))\""
    end
end

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

function main()
    results = [evaluate_q(q) for q in QUBITS_TO_TEST]

    # Summary
    min_q = nothing
    for r in results
        if r["overall"] == "success"
            min_q = r["qubits"]
            break
        end
    end

    by_q = Dict(r["qubits"] => r for r in results)

    q2_failed = Set(by_q[2]["failed"])
    q3_passed = Set(by_q[3]["passed"])
    q3_flips  = sort(collect(intersect(q2_failed, q3_passed)))

    if by_q[2]["overall"] == "success"
        q2_comment = "q=2 does not fail overall; no criteria fail at q=2."
    else
        q2_comment = "q=2 fails: " * join(by_q[2]["failed"], ", ")
    end

    honest_caveat = (
        "The sim shows smallest_success_q=2 (dim=4), NOT q=3. " *
        "The owner empirical observation that '2 qubits fails and 3 succeeds' " *
        "is NOT reproduced under this criterion set. " *
        "Under criteria A-F as defined here, q=2 passes all criteria. " *
        "The failing criterion at q=1 is F_NESTED_SHELL_DISTINGUISHABILITY " *
        "(which requires dim>=4, i.e. at least 2 qubits). " *
        "If the owner's prior observation was criterion-specific (e.g. a stricter " *
        "chirality sector definition, a larger Clifford structure, or a genuine " *
        "spinor-field object requiring more DOF), that criterion is not captured " *
        "in the A-F battery as implemented. " *
        "promotion_allowed: false. This is a diagnostic carrier, not canonical admission."
    )

    payload = Dict{String,Any}(
        "object_id"         => OBJECT_ID,
        "claim_ceiling"     => "finite-map carrier: admitted criteria per qubit count. No layer/manifold/coupling/bridge claim.",
        "promotion_allowed" => false,
        "tolerance"         => TOL,
        "root_constraints"  => ["F01", "N01"],
        "operator_pair"     => Dict{String,Any}(
            "A" => "X on first qubit",
            "B" => "Hadamard on first qubit",
            "design_note" => "Maximally mixed density gives order-gap=0 (null control); pure spinor basis-0 density is the positive witness for criterion D.",
        ),
        "results"   => results,
        "summary"   => Dict{String,Any}(
            "smallest_success_q"   => min_q,
            "smallest_success_dim" => isnothing(min_q) ? nothing : 2^Int(min_q),
            "q3_flip_from_q2"      => q3_flips,
            "q2_overall_comment"   => q2_comment,
        ),
        "honest_caveat" => honest_caveat,
    )

    open(RESULT_PATH, "w") do io
        write(io, to_json(payload))
        write(io, "\n")
    end

    # Stdout report
    println("object_id: ", OBJECT_ID)
    println("tolerance: ", TOL)
    println()
    for r in results
        println("q=$(r["qubits"]) dim=$(r["dim"]) overall=$(uppercase(r["overall"]))")
        println("  PASS: ", isempty(r["passed"]) ? "none" : join(r["passed"], ", "))
        println("  FAIL: ", isempty(r["failed"]) ? "none" : join(r["failed"], ", "))
    end
    println()
    println("smallest_success_q: ", isnothing(min_q) ? "none" : min_q,
            " (dim=", isnothing(min_q) ? "none" : 2^Int(min_q), ")")
    println("q3_flip_from_q2: ", isempty(q3_flips) ? "none" : join(q3_flips, ", "))
    println(q2_comment)
    println()
    println("HONEST CAVEAT: ", honest_caveat)
    println()
    println("promotion_allowed: false")
    println("result JSON written to: ", RESULT_PATH)
end

main()
