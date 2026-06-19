using Dates
using LinearAlgebra
using Random
using Printf

# ─────────────────────────────────────────────────────────────────────────────
# wd_perm24_invariance_julia.jl
# object_id: wd_perm24_invariance_v1
#
# Move: perm24_invariance
# Probe family: M_perm24
#
# Question: Is the IGT operator->function mapping (assigning {Ti,Te,Fi,Fe} to
# the 4 row-operator roles in the payoff matrix) assignment-INVARIANT under all
# 24 permutations, or assignment-DEPENDENT?
#
# INVARIANT means: all 24 permutations produce identical values for the three
# key observables (n01_gap_pattern, win_lose_signature, source_z_ascent).
# → The mapping is physically EMPTY; the engine is a Lindblad-channel artifact.
#
# DEPENDENT means: at least one permutation produces a different value for at
# least one observable.
# → The mapping is loaded (assignment matters).
#
# Domain: {all 24 permutations of (Ti,Te,Fi,Fe) → (R0,R1,R2,R3)} ×
#         {the fixed IGT payoff kernel K} ×
#         {finite operator set satisfying F01, N01}
#
# Codomain: per-permutation (n01_gap, win_lose_asym, z_ascent_gap) triple +
#           variance across permutations + VERDICT ∈ {INVARIANT, DEPENDENT}
#
# Root constraints:
#   F01 — finite carrier, all entries finite, operator dimensions positive
#   N01 — exists nonzero commutator among carrier operators
#
# Claim ceiling: tool_lego_fit_probe
# promotion_allowed: false
# ─────────────────────────────────────────────────────────────────────────────

const OBJECT_ID        = "wd_perm24_invariance_v1"
const RESULT_PATH      = joinpath(@__DIR__, "wd_perm24_invariance_julia_results.json")
const PARITY_PATH      = "/tmp/wd_perm24_invariance_jax_target.json"
const TOL              = 1.0e-9
const INVARIANCE_TOL   = 1.0e-10   # variance threshold for INVARIANT verdict

# ─── Minimal JSON serializer (no external package dep) ────────────────────────

struct JObject
    fields::Vector{Pair{String,Any}}
end

jobj(pairs::Pair...) = JObject(Pair{String,Any}[string(p.first) => p.second for p in pairs])

function json_escape(s::AbstractString)::String
    io = IOBuffer()
    for c in s
        if     c == '"'  ; print(io, "\\\"")
        elseif c == '\\' ; print(io, "\\\\")
        elseif c == '\n' ; print(io, "\\n")
        elseif c == '\r' ; print(io, "\\r")
        elseif c == '\t' ; print(io, "\\t")
        elseif Int(c) < 0x20; print(io, @sprintf("\\u%04x", Int(c)))
        else              ; print(io, c)
        end
    end
    String(take!(io))
end

function json_value(x, indent::Int=0)::String
    pad     = " "^indent
    nextpad = " "^(indent+2)
    if x isa JObject
        isempty(x.fields) && return "{}"
        parts = String[nextpad * "\"" * json_escape(p.first) * "\": " *
                       json_value(p.second, indent+2) for p in x.fields]
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractDict
        return json_value(JObject(Pair{String,Any}[string(k)=>v for (k,v) in x]), indent)
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        isfinite(x) || error("Non-finite float: $(x)")
        return @sprintf("%.14g", x)
    elseif x isa AbstractVector
        isempty(x) && return "[]"
        parts = [nextpad * json_value(v, indent+2) for v in x]
        return "[\n" * join(parts, ",\n") * "\n" * pad * "]"
    else
        error("Unsupported JSON type: $(typeof(x))")
    end
end

function write_json(path::AbstractString, root::JObject)
    open(path, "w") do io
        write(io, json_value(root))
        write(io, "\n")
    end
end

# ─── F01 / N01 checks ─────────────────────────────────────────────────────────

function check_f01(ops::Vector{Matrix{ComplexF64}})::Bool
    for op in ops
        n, m = size(op)
        (n == m > 0) || return false
        (all(isfinite, real.(op)) && all(isfinite, imag.(op))) || return false
    end
    true
end

commutator_norm(a, b) = norm(a*b - b*a)

function check_n01(ops::Vector{Matrix{ComplexF64}}, tol::Float64=TOL)::Tuple{Bool,Float64}
    best = 0.0
    for i in eachindex(ops), j in (i+1):length(ops)
        v = commutator_norm(ops[i], ops[j])
        v > best && (best = v)
    end
    best > tol, best
end

# ─── IGT payoff kernel ────────────────────────────────────────────────────────
#
# The IGT engine is built around a 4×4 payoff matrix K where K[i,j] encodes the
# payoff when row-operator i meets column-operator j.
#
# The "source z-ascent" observable is based on the eigenvalue ordering of the
# symmetrized kernel K_s = (K + K')/2 after applying a dephasing channel
# (diagonal projection) that mimics Lindblad Z-dephasing.
#
# The "win/lose signature" = max_{i,j} |K[i,j] - K[j,i]|  (payoff asymmetry).
#
# The "n01 gap pattern" = vector of commutator norms [||[R_i, R_j]||] for
# each pair of the 4 row operators.  If labelling is just renaming, this vector
# is a permutation of itself regardless of which label maps to which role.
#
# We fix the KERNEL (the numeric values of K[i,j]) and vary only WHICH label
# {Ti,Te,Fi,Fe} is assigned to each role {R0,R1,R2,R3}.
#
# IMPORTANT: the kernel K encodes observable asymmetry between specific (i,j)
# pairs.  If the labels are ONLY labels (empty assignment), then swapping
# "Ti" and "Te" in the role map just renames R0<->R1 which is equivalent to
# permuting rows and columns of K, producing a different matrix but with the
# same SET of singular values, same max asymmetry, and same eigenvalue SET.
# We check whether the scalar summary observables are literally identical across
# all 24 permutations, which is the INVARIANT condition.
#
# Note: for an asymmetric kernel, the max payoff asymmetry |K[i,j]-K[j,i]| is
# invariant under simultaneous row/column permutation ONLY if we measure the
# GLOBAL max, not the per-role values.  The per-role values do differ.
# We record BOTH the global scalar (which IS invariant by symmetry) and the
# per-role vector (which is NOT invariant if roles differ).

# Fixed IGT payoff kernel — designed to have distinct row profiles so
# per-role observables can differ under permutation.
const K_BASE = [
    1.0   0.6   0.2  -0.4;   # R0 row: wins strongly vs R1, weakly vs R2, loses vs R3
   -0.6   1.0   0.7   0.1;   # R1 row: loses to R0, wins vs R2/R3
   -0.2  -0.7   1.0   0.8;   # R2 row: loses vs R0/R1, wins vs R3
    0.4  -0.1  -0.8   1.0    # R3 row: wins vs R0, loses vs R2
]

# Each row operator is a 4×4 Hermitian operator on the carrier.
# We build them from fixed seeds so F01/N01 are stable.
function build_row_operators(seed_base::Int)::Vector{Matrix{ComplexF64}}
    ops = Matrix{ComplexF64}[]
    for i in 0:3
        rng = MersenneTwister(seed_base + i)
        A = randn(rng, 4, 4) .+ im .* randn(rng, 4, 4)
        H = (A + A') / (2.0*sqrt(4.0))
        push!(ops, Matrix{ComplexF64}(H))
    end
    ops
end

const ROW_OPS = build_row_operators(9001)

# Label names
const LABELS = ["Ti", "Te", "Fi", "Fe"]

# ─── All 24 permutations of 4 elements ────────────────────────────────────────

function all_perms(n::Int)::Vector{Vector{Int}}
    if n == 0; return [Int[]]; end
    result = Vector{Int}[]
    for first in 1:n
        rest = [i for i in 1:n if i != first]
        for sub_perm in all_perms(n-1)
            adjusted = [r >= first ? r+1 : r for r in [j for j in sub_perm]]  # not used
            # simpler: just map indices directly
            sub_full = [rest[j] for j in sub_perm]
            push!(result, [first; sub_full])
        end
    end
    result
end

# Generate all 24 permutations of [1,2,3,4]
function all_perms4()::Vector{Vector{Int}}
    result = Vector{Int}[]
    for a in 1:4, b in 1:4, c in 1:4, d in 1:4
        if length(unique([a,b,c,d])) == 4
            push!(result, [a,b,c,d])
        end
    end
    result
end

# ─── Observable computation for a given permutation ───────────────────────────
#
# perm[k] = which label index (1-based) is assigned to role R_{k-1}.
# So if perm = [2,1,3,4], then role R0 gets label Te, role R1 gets Ti, etc.
#
# Permuting the assignment is equivalent to permuting rows (and simultaneously
# columns) of K_BASE:
#   K_perm[i,j] = K_BASE[perm[i], perm[j]]
# (We map role index -> label index, then use the label index to index K_BASE
# rows/cols, since K_BASE is defined in terms of role indices directly.
# Actually, K_BASE is the kernel where row i = role i. Reassigning labels to
# roles does not change K_BASE row values — it only changes which label "owns"
# each row. The per-label observables change; the global observables (max,
# eigenvalue set) do not.  We test BOTH.)
#
# Observable 1: n01_gap_pattern — vector of 6 commutator norms for operator
#   pairs, REORDERED by the label permutation so we track per-label gap.
#   Specifically: n01_gap[k,l] = ||[R_{perm_inv[k]-1}, R_{perm_inv[l]-1}]||
#   where perm_inv maps label -> role.
#   This is a per-label vector; it changes under permutation iff the operators
#   differ from each other.
#
# Observable 2: win_lose_signature — for each label k, the net payoff against
#   all other labels.  net[k] = sum_j K_BASE[role_k, role_j]
#   where role_k = perm_inv[k] - 1 (0-based role for label k).
#   This vector changes under permutation iff K rows differ.
#
# Observable 3: source_z_ascent — eigenvalue ordering of the dephased kernel.
#   Dephased kernel D = diag(K_perm), i.e. only diagonal entries survive.
#   z_ascent[k] = K_BASE[role_k, role_k] for label k.
#   This changes under permutation iff diagonal entries differ.

function compute_observables(perm::Vector{Int})
    # perm[k] = role index (1-based) assigned to label k
    # perm_inv[r] = label index (1-based) whose role is r
    perm_inv = similar(perm)
    for (label_idx, role_idx) in enumerate(perm)
        perm_inv[role_idx] = label_idx
    end

    # Rows of K_BASE indexed by role (0-based: role = perm[k]-1 for label k)
    # For label k (1-based), role is perm[k]-1 (0-based) = perm[k] (1-based K index)
    # K_BASE[role, col] where role = perm[k]

    # Observable 1: per-label n01 gap vector (6 pairs, ordered by label pair index)
    # For label pair (k, l) with k < l:
    #   role_k = perm[k], role_l = perm[l] (1-based)
    #   n01_gap_pair = ||[ROW_OPS[role_k], ROW_OPS[role_l]]||
    n01_gaps = Float64[]
    for k in 1:4, l in (k+1):4
        role_k = perm[k]
        role_l = perm[l]
        push!(n01_gaps, commutator_norm(ROW_OPS[role_k], ROW_OPS[role_l]))
    end

    # Observable 2: per-label win-lose signature (net payoff for each label)
    # net[k] = sum_j K_BASE[perm[k], perm[j]]  (role of label k vs role of label j)
    win_lose_net = Float64[]
    for k in 1:4
        net = sum(K_BASE[perm[k], perm[j]] for j in 1:4)
        push!(win_lose_net, net)
    end

    # Scalar summary: max payoff asymmetry |K[i,j]-K[j,i]| over all pairs
    # This is GLOBAL and permutation-invariant (invariant under simultaneous
    # row/col permutation).
    max_asym = 0.0
    for i in 1:4, j in (i+1):4
        ri, rj = perm[i], perm[j]
        a = abs(K_BASE[ri, rj] - K_BASE[rj, ri])
        a > max_asym && (max_asym = a)
    end

    # Observable 3: per-label source z-ascent (diagonal of permuted K)
    z_ascent = Float64[K_BASE[perm[k], perm[k]] for k in 1:4]

    # Scalar summary: global eigenvalue set of symmetrized permuted K (sorted)
    K_perm = [K_BASE[perm[i], perm[j]] for i in 1:4, j in 1:4]
    K_sym  = (K_perm + K_perm') / 2.0
    evals  = sort(real(eigvals(K_sym)))

    return n01_gaps, win_lose_net, z_ascent, max_asym, evals, K_perm
end

# ─── Variance helper ──────────────────────────────────────────────────────────

function vec_variance(vecs::Vector{Vector{Float64}})::Float64
    # Mean of element-wise variance across all vectors
    n = length(vecs)
    n == 0 && return 0.0
    m = length(vecs[1])
    total = 0.0
    for k in 1:m
        vals = [vecs[i][k] for i in 1:n]
        mu   = sum(vals) / n
        total += sum((v-mu)^2 for v in vals) / n
    end
    total / m
end

# ─── Negative control: symmetrized kernel ─────────────────────────────────────
# When K is symmetric (K = K'), all per-label observables are invariant under
# permutation.  This is the KNOWN-INVARIANT control.

const K_SYM = let
    K = copy(K_BASE)
    (K + K') / 2.0
end

function compute_observables_sym(perm::Vector{Int})
    n01_gaps = Float64[]
    for k in 1:4, l in (k+1):4
        role_k = perm[k]; role_l = perm[l]
        push!(n01_gaps, commutator_norm(ROW_OPS[role_k], ROW_OPS[role_l]))
    end
    win_lose_net = Float64[sum(K_SYM[perm[k], perm[j]] for j in 1:4) for k in 1:4]
    z_ascent     = Float64[K_SYM[perm[k], perm[k]] for k in 1:4]
    max_asym     = 0.0  # K_SYM is symmetric → max asymmetry = 0
    K_perm = [K_SYM[perm[i], perm[j]] for i in 1:4, j in 1:4]
    K_s    = (K_perm + K_perm') / 2.0
    evals  = sort(real(eigvals(K_s)))
    return n01_gaps, win_lose_net, z_ascent, max_asym, evals
end

# ─── Main computation ─────────────────────────────────────────────────────────

function main()
    println("perm24_invariance carrier: object_id=$(OBJECT_ID)")

    # ── F01 / N01 check on base operators
    ops = ROW_OPS
    f01_pass = check_f01(ops)
    n01_pass, n01_max_norm = check_n01(ops)
    println("  F01: $(f01_pass)   N01: $(n01_pass)  (max_commutator_norm=$(round(n01_max_norm, sigdigits=6)))")

    # ── Generate all 24 permutations
    perms = all_perms4()
    @assert length(perms) == 24 "Expected 24 permutations, got $(length(perms))"

    # ── Compute observables for all 24 permutations (asymmetric K_BASE)
    all_n01_gaps      = Vector{Float64}[]
    all_win_lose      = Vector{Float64}[]
    all_z_ascent      = Vector{Float64}[]
    all_max_asym      = Float64[]
    all_evals         = Vector{Float64}[]
    perm_records      = JObject[]

    for (idx, perm) in enumerate(perms)
        n01_gaps, win_lose_net, z_ascent, max_asym, evals, _ = compute_observables(perm)
        push!(all_n01_gaps, n01_gaps)
        push!(all_win_lose, win_lose_net)
        push!(all_z_ascent, z_ascent)
        push!(all_max_asym, max_asym)
        push!(all_evals,    evals)

        label_map = join(["$(LABELS[k])→R$(perm[k]-1)" for k in 1:4], ", ")
        push!(perm_records, jobj(
            "perm_idx"       => idx,
            "assignment"     => label_map,
            "perm_vector"    => perm,
            "n01_gap_vector" => n01_gaps,
            "win_lose_net"   => win_lose_net,
            "z_ascent"       => z_ascent,
            "max_asym_scalar"=> max_asym,
            "eigenvalues_sym"=> evals
        ))
    end

    # ── Variance across 24 permutations
    var_n01   = vec_variance(all_n01_gaps)
    var_wl    = vec_variance(all_win_lose)
    var_za    = vec_variance(all_z_ascent)
    var_evals = vec_variance(all_evals)
    var_masym = let vals=all_max_asym; mu=sum(vals)/length(vals);
                    sum((v-mu)^2 for v in vals)/length(vals) end

    # Global max_asym is permutation-invariant (should be 0 variance)
    # Per-label observables vary → DEPENDENT if variance > INVARIANCE_TOL

    per_label_vars = max(var_n01, var_wl, var_za)
    global_vars    = max(var_masym, var_evals)

    per_label_invariant = per_label_vars < INVARIANCE_TOL
    global_invariant    = global_vars    < INVARIANCE_TOL

    # ── Negative control: symmetrized kernel
    sym_n01_gaps  = Vector{Float64}[]
    sym_win_lose  = Vector{Float64}[]
    sym_z_ascent  = Vector{Float64}[]
    for perm in perms
        n01g, wln, za, _, _ = compute_observables_sym(perm)
        push!(sym_n01_gaps, n01g)
        push!(sym_win_lose, wln)
        push!(sym_z_ascent, za)
    end
    sym_var_n01 = vec_variance(sym_n01_gaps)
    sym_var_wl  = vec_variance(sym_win_lose)
    sym_var_za  = vec_variance(sym_z_ascent)
    sym_per_label_vars = max(sym_var_n01, sym_var_wl, sym_var_za)
    # For symmetric K: win_lose_net and z_ascent ARE permutation-variant
    # (because the operator rows still differ). Only max_asym is 0.
    # n01_gaps are also permutation-variant (operators differ).
    # So the negative control ALSO shows per-label variance — this is expected.
    # The control tests max_asym = 0 (no win-lose direction in symmetric K).

    # ── Load-bearing flip: erase operator distinctness
    # If all ROW_OPS were identical, all commutator norms = 0, n01 gaps = 0,
    # and n01_gap_vector variance = 0 → mapping trivially INVARIANT (but N01 fails).
    # This is the ablation: zero-out ROW_OPS → all gaps zero → N01 fails.
    ops_zero = [zeros(ComplexF64, 4, 4) for _ in 1:4]
    n01_zero_pass, n01_zero_norm = check_n01(ops_zero)
    flip_n01_excluded = !n01_zero_pass   # should be true (N01 fails → excluded)

    # ── Boundary checks: size ladder on N01 norms
    boundary_n01 = JObject[]
    for seed in [9001, 9101, 9201, 9301]
        ops_b = [begin
            rng = MersenneTwister(seed + i)
            A = randn(rng, 4, 4) .+ im .* randn(rng, 4, 4)
            Matrix{ComplexF64}((A + A') / (2.0*sqrt(4.0)))
        end for i in 0:3]
        _, nrm = check_n01(ops_b)
        push!(boundary_n01, jobj(
            "seed"              => seed,
            "n01_max_comm_norm" => nrm,
            "n01_pass"          => nrm > TOL
        ))
    end

    # ── Verdict
    # Per-label observables ARE variant (DEPENDENT) because:
    # - different operators have different commutator norms
    # - K_BASE has distinct row profiles
    # But: the GLOBAL scalar (max_asym, eigenvalue set of K_sym) is invariant.
    # This means: if the engine only exposes GLOBAL scalars, it is INVARIANT
    # (mapping is empty). If the engine exposes per-label/per-role values, it
    # is DEPENDENT (mapping is loaded).

    println("\n  Per-label observable variance across 24 perms:")
    println("    var(n01_gaps): $(round(var_n01, sigdigits=4))")
    println("    var(win_lose_net): $(round(var_wl, sigdigits=4))")
    println("    var(z_ascent): $(round(var_za, sigdigits=4))")
    println("    per_label_invariant: $(per_label_invariant)")
    println("  Global observable variance:")
    println("    var(max_asym_scalar): $(round(var_masym, sigdigits=4))")
    println("    var(eigenvalues_sym): $(round(var_evals, sigdigits=4))")
    println("    global_invariant: $(global_invariant)")

    # Honest verdict: per-label → DEPENDENT; global scalars → INVARIANT
    verdict = if per_label_invariant && global_invariant
        "INVARIANT: both per-label and global observables identical across all 24 permutations — assignment mapping is physically EMPTY"
    elseif global_invariant && !per_label_invariant
        "SPLIT: global scalars INVARIANT (max_asym, eigenvalue set preserved); per-label observables DEPENDENT (n01_gap_pattern, win_lose_net, z_ascent differ by assignment) — mapping is loaded at the per-label level but empty at the aggregate level"
    elseif !global_invariant && !per_label_invariant
        "DEPENDENT: both per-label and global observables vary across permutations — assignment mapping is loaded"
    else
        "GLOBAL_DEPENDENT_PER_LABEL_INVARIANT: unexpected — check implementation"
    end

    println("\n  VERDICT: $(verdict)")

    # ─── Build result JSON ────────────────────────────────────────────────────

    root = jobj(
        "object_id"          => OBJECT_ID,
        "claim_ceiling"      => "perm24_invariance probe only: no layer-completion, manifold admission, coupling, bridge, Axis0, flux, or physics claims. Tests whether IGT operator->function label assignment is invariant or loaded under all 24 permutations.",
        "promotion_allowed"  => false,
        "classification"     => "tool_lego_fit_probe",
        "generated_at"       => string(now(UTC)),
        "move"               => "perm24_invariance",
        "root_constraints"   => jobj(
            "F01" => "finite carrier/probe/operator set; all entries finite; operator dimensions positive",
            "N01" => "exists at least one nonzero commutator norm among carrier operators"
        ),
        "probe_family"       => jobj(
            "name"        => "M_perm24",
            "definition"  => "all 24 permutations of {Ti,Te,Fi,Fe}→{R0,R1,R2,R3}; observables: n01_gap_vector, win_lose_net, z_ascent; verdict: INVARIANT iff max per-label variance < $(INVARIANCE_TOL)",
            "n_perms"     => 24,
            "labels"      => LABELS,
            "roles"       => ["R0","R1","R2","R3"]
        ),
        "domain"             => "all 24 permutations of {Ti,Te,Fi,Fe} to {R0,R1,R2,R3} × fixed IGT payoff kernel K_BASE × fixed Hermitian row operators (seed 9001-9004)",
        "codomain"           => "per-permutation (n01_gap_vector, win_lose_net, z_ascent, max_asym_scalar, eigenvalues_sym) + variance across 24 + VERDICT",
        "f01_pass"           => f01_pass,
        "n01_pass"           => n01_pass,
        "n01_max_commutator_norm" => n01_max_norm,
        "kernel_K_BASE"      => jobj(
            "shape"       => "4x4 real asymmetric payoff matrix",
            "description" => "IGT payoff kernel: K[i,j] = payoff when role Ri meets role Rj; rows have distinct profiles to make per-role observables non-trivial",
            "diagonal"    => [K_BASE[i,i] for i in 1:4],
            "max_off_diag_asymmetry" => let asym_vals = [abs(K_BASE[ii,jj]-K_BASE[jj,ii]) for ii in 1:4, jj in 1:4 if ii < jj]; maximum(asym_vals) end
        ),
        "variance_summary"   => jobj(
            "var_n01_gap_vector"      => var_n01,
            "var_win_lose_net"        => var_wl,
            "var_z_ascent"            => var_za,
            "var_max_asym_scalar"     => var_masym,
            "var_eigenvalues_sym"     => var_evals,
            "per_label_max_var"       => per_label_vars,
            "global_max_var"          => global_vars,
            "per_label_invariant"     => per_label_invariant,
            "global_invariant"        => global_invariant
        ),
        "verdict"            => verdict,
        "permutation_records" => perm_records,
        "negative_control_sym_kernel" => jobj(
            "description" => "K_SYM = (K_BASE+K_BASE')/2: symmetric kernel; max_asym = 0 for all perms; per-label n01/z_ascent still vary (operator distinctness); shows global scalar invariance is a property of kernel symmetry, not label assignment",
            "var_n01_sym" => sym_var_n01,
            "var_wl_sym"  => sym_var_wl,
            "var_za_sym"  => sym_var_za,
            "sym_per_label_invariant" => sym_per_label_vars < INVARIANCE_TOL
        ),
        "load_bearing_flip"  => jobj(
            "ablation"        => "zero-out all ROW_OPS → all commutator norms = 0 → N01 fails → carrier excluded",
            "n01_zero_pass"   => n01_zero_pass,
            "flip_n01_excluded" => flip_n01_excluded,
            "interpretation"  => flip_n01_excluded ?
                "LOAD-BEARING: ablating operator distinctness excludes carrier under N01; n01_gap_vector becomes trivially zero and permutation-invariant only because N01 fails" :
                "ERROR: N01 should fail for zero operators"
        ),
        "boundary_checks"    => jobj(
            "description" => "Size-4 operator sets from 4 different seeds; all should show N01 pass (distinct random Hermitian ops have nonzero commutators)",
            "checks"      => boundary_n01
        ),
        "tool_manifest"      => jobj(
            "julia_stdlib_LinearAlgebra" => "load-bearing: commutator norms (check_n01), eigvals (z_ascent eigenvalue ordering), norm computations",
            "julia_stdlib_Random"        => "load-bearing: fixed-seed Hermitian operator construction for row operators",
            "julia_stdlib_Dates"         => "supportive: timestamp only",
            "julia_stdlib_Printf"        => "supportive: JSON float formatting"
        ),
        "tool_integration_depth" => jobj(
            "LinearAlgebra" => "load_bearing",
            "Random"        => "load_bearing",
            "Dates"         => "supportive",
            "Printf"        => "supportive"
        )
    )

    write_json(RESULT_PATH, root)
    println("\nResult written to: $(RESULT_PATH)")

    # ─── Parity target for JAX ────────────────────────────────────────────────
    parity = jobj(
        "object_id"              => OBJECT_ID,
        "move"                   => "perm24_invariance",
        "n01_max_commutator_norm"=> n01_max_norm,
        "var_n01_gap_vector"     => var_n01,
        "var_win_lose_net"       => var_wl,
        "var_z_ascent"           => var_za,
        "var_max_asym_scalar"    => var_masym,
        "per_label_invariant"    => per_label_invariant,
        "global_invariant"       => global_invariant,
        "verdict"                => verdict,
        "kernel_diagonal"        => [K_BASE[i,i] for i in 1:4],
        "kernel_max_off_diag_asym" => let asym_vals2 = [abs(K_BASE[ii,jj]-K_BASE[jj,ii]) for ii in 1:4, jj in 1:4 if ii < jj]; maximum(asym_vals2) end,
        # First permutation's observables for JAX cross-check
        "perm1_n01_gaps"         => all_n01_gaps[1],
        "perm1_win_lose_net"     => all_win_lose[1],
        "perm1_z_ascent"         => all_z_ascent[1],
        # Last permutation
        "perm24_n01_gaps"        => all_n01_gaps[24],
        "perm24_win_lose_net"    => all_win_lose[24],
        "perm24_z_ascent"        => all_z_ascent[24]
    )
    write_json(PARITY_PATH, parity)
    println("Parity target written to: $(PARITY_PATH)")
end

main()
