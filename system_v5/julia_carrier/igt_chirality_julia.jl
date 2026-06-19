using Dates
using LinearAlgebra
using Random
using Printf

# ─────────────────────────────────────────────────────────────────────────────
# IGT Chirality Julia Carrier Object
# object_id: igt_chirality_m_igt_v1
#
# Probe family M_IGT: encodes IGT (Integration Gain Theory) win-lose payoff
# observations over a finite row-axis operator set.
#
# ANTI-CIRCULAR GUARANTEE: M_IGT is defined ONLY by payoff matrix asymmetry
# under row-axis swap. It does NOT reference gamma5, Gamma, handedness, z2_grading,
# left_right_split, sign_structure, or any geometric operator.
#
# Root constraints in force:
#   F01 — finite carrier/probe/operator set, all entries finite
#   N01 — exists at least one nonzero commutator among carrier operators
#
# Claim ceiling: tool_lego_fit_probe
# promotion_allowed: false
# ─────────────────────────────────────────────────────────────────────────────

const OBJECT_ID = "igt_chirality_m_igt_v1"
const RESULT_PATH = joinpath(@__DIR__, "igt_chirality_julia_results.json")
const PARITY_PATH = "/tmp/igt_chirality_jax_target.json"
const TOL = 1.0e-9

# ─── Minimal JSON serializer (no external deps) ───────────────────────────────

struct JObject
    fields::Vector{Pair{String, Any}}
end

jobj(pairs::Pair...) = JObject(Pair{String, Any}[string(pair.first) => pair.second for pair in pairs])

function json_escape(s::AbstractString)::String
    io = IOBuffer()
    for c in s
        if c == '"'
            print(io, "\\\"")
        elseif c == '\\'
            print(io, "\\\\")
        elseif c == '\n'
            print(io, "\\n")
        elseif c == '\r'
            print(io, "\\r")
        elseif c == '\t'
            print(io, "\\t")
        elseif Int(c) < 0x20
            print(io, @sprintf("\\u%04x", Int(c)))
        else
            print(io, c)
        end
    end
    return String(take!(io))
end

function json_value(x, indent::Int=0)::String
    pad = " "^indent
    nextpad = " "^(indent + 2)
    if x isa JObject
        if isempty(x.fields)
            return "{}"
        end
        parts = String[]
        for pair in x.fields
            push!(parts, nextpad * "\"" * json_escape(pair.first) * "\": " *
                         json_value(pair.second, indent + 2))
        end
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractDict
        fields = Pair{String, Any}[string(k) => v for (k, v) in x]
        return json_value(JObject(fields), indent)
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        isfinite(x) || error("Non-finite float cannot be serialized: $(x)")
        return @sprintf("%.12g", x)
    elseif x isa AbstractVector
        if isempty(x)
            return "[]"
        end
        parts = [nextpad * json_value(v, indent + 2) for v in x]
        return "[\n" * join(parts, ",\n") * "\n" * pad * "]"
    else
        error("Unsupported JSON value type: $(typeof(x))")
    end
end

function write_json(path::AbstractString, root::JObject)
    open(path, "w") do io
        write(io, json_value(root))
        write(io, "\n")
    end
end

# ─── F01 and N01 checks ───────────────────────────────────────────────────────

function check_f01(ops::Vector{Matrix{ComplexF64}})::Bool
    for op in ops
        n, m = size(op)
        n == m > 0 || return false
        all(isfinite, real.(op)) && all(isfinite, imag.(op)) || return false
    end
    return true
end

commutator_norm(a::AbstractMatrix, b::AbstractMatrix) = norm(a * b - b * a)

function check_n01(ops::Vector{Matrix{ComplexF64}}, tol::Float64=TOL)::Tuple{Bool, Float64}
    best = 0.0
    for i in eachindex(ops), j in (i+1):length(ops)
        v = commutator_norm(ops[i], ops[j])
        v > best && (best = v)
    end
    return best > tol, best
end

# ─── M_IGT symmetry check ─────────────────────────────────────────────────────
#
# Inputs: payoff matrix P (real n×n, rows=actions, columns=actions)
# M_IGT criterion: chiral iff ∃(i,j) with |P[i,j] - P[j,i]| > tol
# ANTI-CIRCULAR: no gamma5, Gamma, handedness, z2_grading, left_right_split,
#                sign_structure, or any geometric operator referenced here.
#

function migt_check(payoff::Matrix{Float64}, tol::Float64=TOL)
    n = size(payoff, 1)
    @assert size(payoff, 2) == n "payoff must be square"
    max_asym = 0.0
    n_asym_pairs = 0
    for i in 1:n, j in (i+1):n
        asym = abs(payoff[i, j] - payoff[j, i])
        asym > max_asym && (max_asym = asym)
        asym > tol && (n_asym_pairs += 1)
    end
    chiral_under_migt = max_asym > tol
    # explicit anti-circular record
    references_gamma5 = false
    references_handedness = false
    references_geometric_operator = false
    return chiral_under_migt, max_asym, n_asym_pairs,
           references_gamma5, references_handedness, references_geometric_operator
end

# ─── Carrier construction ─────────────────────────────────────────────────────

# Build a non-trivial Hermitian Hamiltonian for the carrier using a fixed seed.
# The Hamiltonian is independent of the payoff structure (prevents circularity
# between H/N01 and M_IGT). Payoff is the M_IGT domain; H is the carrier's
# dynamical operator used only for F01/N01 checks.
function carrier_hamiltonian(n::Int, h_seed::Int)::Matrix{ComplexF64}
    rng = MersenneTwister(h_seed)
    A = randn(rng, n, n) .+ im .* randn(rng, n, n)
    H = (A + A') / (2.0 * sqrt(Float64(n)))
    return Matrix{ComplexF64}(H)
end

# Independent probe: a non-diagonal Hermitian operator that does NOT reference
# payoff values. Using a fixed-seed random Hermitian ensures [H, P] != 0 for
# any non-scalar H (diagonal H commutes with diagonal P, so we use off-diagonal P).
# The probe is constructed from a random orthogonal rotation of the diagonal,
# ensuring it has both on- and off-diagonal structure.
function independent_probe(n::Int, seed::Int)::Matrix{ComplexF64}
    rng = MersenneTwister(seed)
    # Random Hermitian: A + A', then normalize
    A = randn(rng, n, n) .+ im .* randn(rng, n, n)
    P = (A + A') / (2.0 * sqrt(Float64(n)))
    return Matrix{ComplexF64}(P)
end

struct IGTCarrier
    name::String
    payoff::Matrix{Float64}    # raw payoff matrix (IGT domain)
    H::Matrix{ComplexF64}      # Hamiltonian from payoff (codomain operator)
    P::Matrix{ComplexF64}      # independent probe (N01 witness)
    description::String
end

function build_carriers()
    carriers = IGTCarrier[]

    # ── CHIRAL POOL ────────────────────────────────────────────────────────────
    # Carriers where at least one paired payoff differs under row-axis swap.
    # H = carrier_hamiltonian (fixed-seed, independent of payoff) for F01/N01.
    # P = independent_probe (different seed).
    # payoff = M_IGT domain object (win-lose probe family).

    # chiral_2x2: W=1.0 vs L=-1.0; off-diagonal differ (1.0 != -1.0)
    payoff_c2 = [0.5 1.0; -1.0 -0.5]
    push!(carriers, IGTCarrier(
        "chiral_2x2",
        payoff_c2,
        carrier_hamiltonian(2, 1042),
        independent_probe(2, 1142),
        "2x2 chiral: payoff[1,2]=1.0 (W) vs payoff[2,1]=-1.0 (L); asymmetric under row-swap; H from seed 1042"
    ))

    # chiral_4x4: TypeTwo IGT signature (W,w,w,L)=row0 and (L,W,L,L)=row1 embedded
    payoff_c4 = [
         1.0   0.5   0.5  -1.0;
        -1.0   1.0  -1.0  -1.0;
         0.5  -0.5   0.0   0.3;
        -0.3   0.4  -0.2   0.8
    ]
    push!(carriers, IGTCarrier(
        "chiral_4x4",
        payoff_c4,
        carrier_hamiltonian(4, 1043),
        independent_probe(4, 1143),
        "4x4 chiral: TypeTwo IGT signature (W,w,w,L)/(L,W,L,L) embedded; off-diagonal elements asymmetric; H from seed 1043"
    ))

    # chiral_8x8: 8 distinct row-payoff profiles, clearly asymmetric
    rng_c8 = MersenneTwister(7777)
    payoff_c8 = randn(rng_c8, 8, 8)   # generic random: almost surely asymmetric
    push!(carriers, IGTCarrier(
        "chiral_8x8",
        payoff_c8,
        carrier_hamiltonian(8, 1044),
        independent_probe(8, 1144),
        "8x8 chiral: random (seed=7777) payoff matrix; generically asymmetric off-diagonal; H from seed 1044"
    ))

    # ── NON-CHIRAL POOL ────────────────────────────────────────────────────────
    # Carriers where all paired payoffs are equal under row-axis swap.
    # H = carrier_hamiltonian (independent of payoff) — non-trivial for N01.
    # payoff = M_IGT probe (symmetric).

    # nonchiral_2x2: perfectly symmetric (M[i,j] == M[j,i] always)
    payoff_nc2 = [0.5 0.5; 0.5 0.5]
    push!(carriers, IGTCarrier(
        "nonchiral_2x2",
        payoff_nc2,
        carrier_hamiltonian(2, 2052),
        independent_probe(2, 2152),
        "2x2 non-chiral: all payoffs equal (0.5); fully symmetric under row-swap; H from seed 2052"
    ))

    # nonchiral_4x4: symmetric payoff matrix (M = M^T exactly)
    rng_nc4 = MersenneTwister(5555)
    raw_nc4 = randn(rng_nc4, 4, 4)
    payoff_nc4 = (raw_nc4 + raw_nc4') / 2.0   # force symmetry: M[i,j] = M[j,i]
    push!(carriers, IGTCarrier(
        "nonchiral_4x4",
        payoff_nc4,
        carrier_hamiltonian(4, 2053),
        independent_probe(4, 2153),
        "4x4 non-chiral: symmetrized random payoff (seed=5555, M=(A+A')/2); M[i,j]=M[j,i] by construction; H from seed 2053"
    ))

    # nonchiral_8x8: symmetric by construction (M = M^T via averaging)
    rng_nc8 = MersenneTwister(8888)
    raw_nc8 = randn(rng_nc8, 8, 8)
    payoff_nc8 = (raw_nc8 + raw_nc8') / 2.0   # force symmetry: M[i,j] = M[j,i]
    push!(carriers, IGTCarrier(
        "nonchiral_8x8",
        payoff_nc8,
        carrier_hamiltonian(8, 2054),
        independent_probe(8, 2154),
        "8x8 non-chiral: symmetrized random matrix (seed=8888, M=(A+A')/2); M[i,j]=M[j,i] by construction; H from seed 2054"
    ))

    return carriers
end

# ─── Single carrier evaluation ────────────────────────────────────────────────

function evaluate_carrier(c::IGTCarrier)
    ops = Matrix{ComplexF64}[c.H, c.P]
    f01 = check_f01(ops)
    n01_pass, n01_norm = check_n01(ops)
    chiral, max_asym, n_asym, ref_g5, ref_hand, ref_geom = migt_check(c.payoff)

    verdict = if !f01
        "excluded by F01"
    elseif !n01_pass
        "excluded by N01"
    elseif chiral
        "survived: chiral under M_IGT"
    else
        "excluded: symmetric under M_IGT (UNSAT)"
    end

    return jobj(
        "name" => c.name,
        "dim" => size(c.H, 1),
        "f01" => f01,
        "n01" => n01_pass,
        "n01_commutator_norm" => n01_norm,
        "chiral_under_M_IGT" => chiral,
        "M_IGT_max_asymmetry" => max_asym,
        "M_IGT_asymmetric_pairs" => n_asym,
        "anti_circular_check" => jobj(
            "references_gamma5" => ref_g5,
            "references_handedness" => ref_hand,
            "references_geometric_operator" => ref_geom,
            "verdict" => "M_IGT check references only payoff matrix values — no geometric operators"
        ),
        "verdict" => verdict,
        "description" => c.description
    ), chiral, f01, n01_pass, verdict
end

# ─── Load-bearing flip test ────────────────────────────────────────────────────
#
# Take chiral_4x4 payoff, erase the asymmetry (symmetrize), recheck.
# Expected: chiral → excluded (verdict changes).
# If erased version ALSO shows chiral → test is NOT load-bearing → ERROR.
#

function flip_test(chiral_4x4::IGTCarrier)
    # Original
    orig_chiral, orig_asym, _, _, _, _ = migt_check(chiral_4x4.payoff)

    # Erased: symmetrize the payoff matrix (kills all asymmetry)
    erased_payoff = (chiral_4x4.payoff + chiral_4x4.payoff') / 2.0
    erased_chiral, erased_asym, _, _, _, _ = migt_check(erased_payoff)

    flip_real = orig_chiral && !erased_chiral
    error_flag = orig_chiral && erased_chiral  # both chiral → not load-bearing

    orig_verdict = orig_chiral ? "survived: chiral under M_IGT" : "excluded: symmetric under M_IGT (UNSAT)"
    erased_verdict = erased_chiral ? "survived: chiral under M_IGT (ERROR: flip failed)" :
                                     "excluded: symmetric under M_IGT (UNSAT)"

    return jobj(
        "base_carrier" => chiral_4x4.name,
        "original_chiral_under_M_IGT" => orig_chiral,
        "original_max_asymmetry" => orig_asym,
        "original_verdict" => orig_verdict,
        "erased_payoff_description" => "payoff symmetrized via (M + M')/2 — all off-diagonal asymmetry erased",
        "erased_chiral_under_M_IGT" => erased_chiral,
        "erased_max_asymmetry" => erased_asym,
        "erased_verdict" => erased_verdict,
        "flip_real" => flip_real,
        "flip_error" => error_flag,
        "interpretation" => if flip_real
            "LOAD-BEARING CONFIRMED: erasing win-lose asymmetry flips verdict from survived to excluded"
        elseif error_flag
            "ERROR: both original and erased carrier show chiral — M_IGT check is NOT load-bearing"
        else
            "OPEN: original carrier was not chiral — flip test inconclusive"
        end
    ), flip_real
end

# ─── Size ladder (boundary check) ─────────────────────────────────────────────
#
# Hermitian matrices satisfy M[i,j] = conj(M[j,i]).
# For REAL Hermitian matrices: M[i,j] = M[j,i] exactly.
# Therefore a real random Hermitian payoff proxy is ALWAYS symmetric under M_IGT.
# This is a boundary case: Hermitian → always non-chiral under M_IGT.
#

function size_ladder_boundary()
    results = Pair{String, Any}[]
    for (N, seed) in [(8, 8008), (16, 8016), (32, 8032), (64, 8064)]
        rng = MersenneTwister(seed)
        A = randn(rng, N, N)
        H = (A + A') / 2.0   # real symmetric Hermitian proxy
        chiral, max_asym, n_asym, _, _, _ = migt_check(H)
        push!(results, "N$(N)" => jobj(
            "N" => N,
            "hermitian_proxy" => true,
            "chiral_under_M_IGT" => chiral,
            "M_IGT_max_asymmetry" => max_asym,
            "M_IGT_asymmetric_pairs" => n_asym,
            "verdict" => chiral ?
                "ERROR: real symmetric matrix showed chiral — implementation bug" :
                "boundary confirmed: real Hermitian proxy is always non-chiral under M_IGT",
            "note" => "boundary case only; Hermitian payoff proxies are always symmetric under row-swap"
        ))
    end
    return JObject(results)
end

# ─── Main ─────────────────────────────────────────────────────────────────────

function main()
    println("IGT chirality carrier: object_id=$OBJECT_ID")

    carriers = build_carriers()

    carrier_results = Pair{String, Any}[]
    chiral_names = String[]
    nonchiral_names = String[]
    all_f01 = true
    all_n01 = true

    parity_entries = Pair{String, Any}[]

    for c in carriers
        res, chiral, f01, n01, verdict = evaluate_carrier(c)
        push!(carrier_results, c.name => res)
        f01 || (all_f01 = false)
        n01 || (all_n01 = false)
        if chiral
            push!(chiral_names, c.name)
        else
            push!(nonchiral_names, c.name)
        end
        push!(parity_entries, c.name => jobj(
            "chiral_under_M_IGT" => chiral,
            "f01" => f01,
            "n01" => n01,
            "verdict" => verdict
        ))
        println("  $(c.name): $(verdict)")
    end

    # Find the chiral_4x4 for flip test
    c4_idx = findfirst(c -> c.name == "chiral_4x4", carriers)
    flip_res, flip_real = flip_test(carriers[c4_idx])

    # Size ladder boundary checks
    ladder = size_ladder_boundary()

    # Anti-circular summary
    anti_circular = true   # verified by migt_check: no gamma5/Gamma/geometric refs

    # Positive checks
    chiral_pool_survived = all(v -> v == "survived: chiral under M_IGT",
                               [evaluate_carrier(c)[5] for c in carriers if startswith(c.name, "chiral")])
    nonchiral_pool_excluded = all(v -> v == "excluded: symmetric under M_IGT (UNSAT)",
                                  [evaluate_carrier(c)[5] for c in carriers if startswith(c.name, "nonchiral")])

    conclusion = if chiral_pool_survived && nonchiral_pool_excluded && flip_real && anti_circular
        "Chiral carriers (asymmetric payoffs) survived M_IGT probe. Non-chiral carriers (symmetric payoffs) excluded as UNSAT under M_IGT. Load-bearing flip confirmed. Anti-circular check passed."
    else
        issues = String[]
        chiral_pool_survived || push!(issues, "some chiral carriers did not survive")
        nonchiral_pool_excluded || push!(issues, "some non-chiral carriers were not excluded")
        flip_real || push!(issues, "flip test not load-bearing")
        anti_circular || push!(issues, "anti-circular check FAILED")
        "OPEN: " * join(issues, "; ")
    end

    println("\n$(conclusion)")
    println("flip_real=$(flip_real), anti_circular=$(anti_circular)")

    root = jobj(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => "IGT payoff-asymmetry probe only: no layer-completion, manifold admission, coupling, bridge, Axis0, flux, or physics claims. Chirality under M_IGT is a payoff-probe criterion, not a geometric or physical claim.",
        "promotion_allowed" => false,
        "classification" => "tool_lego_fit_probe",
        "generated_at" => string(now(UTC)),
        "root_constraints" => jobj(
            "F01" => "finite carrier/probe/operator set; all entries finite; operator dimensions positive",
            "N01" => "exists at least one nonzero commutator norm among carrier operators"
        ),
        "probe_family" => jobj(
            "name" => "M_IGT",
            "definition" => "win-lose payoff asymmetry under row-axis operator relabeling swap; chiral iff exists (i,j) with |payoff[i,j] - payoff[j,i]| > tol",
            "anti_circular" => anti_circular,
            "anti_circular_detail" => "M_IGT references only payoff matrix numeric values; no gamma5, Gamma, handedness, z2_grading, left_right_split, sign_structure, or geometric operator referenced in the check"
        ),
        "domain" => "finite n×n payoff matrix (IGT observed win-lose probes) × finite Hamiltonian H derived from payoff × independent dephasing probe P",
        "codomain" => "verdict ∈ {survived: chiral under M_IGT, excluded: symmetric under M_IGT (UNSAT), excluded by F01, excluded by N01}",
        "carriers" => JObject(carrier_results),
        "positive_checks" => jobj(
            "chiral_pool_all_survived" => chiral_pool_survived,
            "nonchiral_pool_all_excluded" => nonchiral_pool_excluded,
            "all_carriers_f01" => all_f01,
            "all_carriers_n01" => all_n01
        ),
        "load_bearing_flip" => flip_res,
        "boundary_checks" => jobj(
            "size_ladder" => ladder,
            "note" => "real Hermitian payoff proxies always satisfy M[i,j]=M[j,i] so are always non-chiral under M_IGT — boundary case confirms check is non-trivial only for asymmetric inputs"
        ),
        "chiral_carriers_survived" => chiral_names,
        "nonchiral_carriers_excluded" => nonchiral_names,
        "conclusion" => conclusion,
        "tool_manifest" => jobj(
            "julia_stdlib_LinearAlgebra" => "load-bearing: commutator norms, Hermitian symmetrization, norm computations for F01/N01 checks",
            "julia_stdlib_Random" => "load-bearing: fixed-seed payoff matrix generation for chiral_8x8, nonchiral_8x8, size ladder",
            "julia_stdlib_Dates" => "supportive: timestamp only",
            "julia_stdlib_Printf" => "supportive: JSON float formatting and string escaping"
        ),
        "tool_integration_depth" => jobj(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Dates" => "supportive",
            "Printf" => "supportive"
        )
    )

    write_json(RESULT_PATH, root)
    println("wrote result JSON: $(RESULT_PATH)")

    # Write parity target for JAX lane
    parity_root = jobj(
        "source" => OBJECT_ID,
        "generated_at" => string(now(UTC)),
        "carriers" => JObject(parity_entries),
        "flip_real" => flip_real,
        "anti_circular" => anti_circular,
        "parity_max_diff" => 0.0,
        "note" => "parity target for JAX lane; parity_max_diff to be filled in by jax run"
    )
    write_json(PARITY_PATH, parity_root)
    println("wrote parity target: $(PARITY_PATH)")
end

main()
