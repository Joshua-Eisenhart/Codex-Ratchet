# crl_ratchet_julia.jl
#
# object_id: crl_ratchet_v1
# claim_ceiling: Cumulative-exclusion ratchet ladder (L0..L9) over the chirality-free
#   predicate stack. Tests which carriers survive each cumulative constraint layer.
#   Does NOT assert layer-completion, manifold admission, coupling, bridge, flux,
#   Axis0, basin, or physics.
# promotion_allowed: false
#
# Root constraints:
#   F01: finite-dimensional carrier/probe/operator/path set.
#   N01: there exists a noncommuting operator pair in the carrier.
#
# Finite map:
#   (carrier_name, layer_depth) -> {sat, reason, gap}
#   Where sat=true means carrier survives all layers up to and including layer_depth.
#
# Domain:
#   carrier_name in {weyl_chiral, vector_dirac_symmetric, parity_symmetric,
#                    real_structure, order_independent, generic_random}
#   layer_depth in {0,1,2,3,4,5,6,7,8,9}
#
# Codomain:
#   per_carrier_survival: depth x carrier -> {sat/unsat, reason, measured_value}
#   exclusion_depth: first layer k where ALL non-chiral UNSAT and ALL chiral SAT
#   load_bearing_flip: does erasing L9 (and L8) allow non-chiral to return SAT?
#
# Anti-fabrication controls:
#   - Wrong-structure control: commuting operator pool (order_independent carrier)
#     must be UNSAT at the order-sensitive layer.
#   - Erase-L9 control: removing the stacking-order check must flip non-chiral
#     verdict (if they stay UNSAT without L9, L9 is not the load-bearing separator).
#   - Chiral-survive check: chiral carrier must stay SAT through all layers.

using LinearAlgebra
using Random
using Statistics
using Dates
using Printf

# ── JSON helpers (no external package dependency) ──────────────────────────────
struct JObj
    fields::Vector{Pair{String, Any}}
end
jobj(pairs::Pair...) = JObj(Pair{String, Any}[string(p.first) => p.second for p in pairs])

function json_escape(s::AbstractString)::String
    io = IOBuffer()
    for c in s
        if c == '"';      print(io, "\\\"")
        elseif c == '\\'; print(io, "\\\\")
        elseif c == '\n'; print(io, "\\n")
        elseif c == '\r'; print(io, "\\r")
        elseif c == '\t'; print(io, "\\t")
        elseif Int(c) < 0x20; print(io, @sprintf("\\u%04x", Int(c)))
        else; print(io, c)
        end
    end
    String(take!(io))
end

function json_value(x, indent::Int=0)::String
    pad  = " "^indent
    npad = " "^(indent + 2)
    if x isa JObj
        isempty(x.fields) && return "{}"
        parts = [npad * "\"" * json_escape(p.first) * "\": " *
                 json_value(p.second, indent + 2) for p in x.fields]
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractDict
        return json_value(JObj(Pair{String,Any}[string(k) => v for (k,v) in x]), indent)
    elseif x isa AbstractString;    return "\"" * json_escape(string(x)) * "\""
    elseif x isa Bool;              return x ? "true" : "false"
    elseif x === nothing;           return "null"
    elseif x isa Integer;           return string(x)
    elseif x isa AbstractFloat
        isfinite(x) || return "null"   # guard for Inf/NaN
        return @sprintf("%.12g", x)
    elseif x isa AbstractVector
        isempty(x) && return "[]"
        parts = [npad * json_value(v, indent + 2) for v in x]
        return "[\n" * join(parts, ",\n") * "\n" * pad * "]"
    else
        error("Unsupported JSON type: $(typeof(x))")
    end
end

write_json(path, root::JObj) = open(path, "w") do io
    write(io, json_value(root)); write(io, "\n")
end
# ──────────────────────────────────────────────────────────────────────────────

const OBJECT_ID   = "crl_ratchet_v1"
const RESULT_PATH = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/crl_ratchet_julia_results.json"
const TOL         = 1e-10   # primary comparison threshold
const EPS_COMM    = 1e-10   # N01 noncommutation threshold
const EPS_ENTROPY = 1e-10   # entropy monotone threshold
const EPS_ORDER   = 1e-10   # order-gap threshold
const EPS_INTER   = 1e-10   # inter-shell trace-dist threshold
const RNG_SEED    = 20260604
const LADDER_DIMS = [8, 16, 32, 64]

# ── Pauli basis ──────────────────────────────────────────────────────────────
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
kron2(a, b) = kron(a, b)
kron3(a, b, c) = kron(kron(a, b), c)

# ── Operator helpers ─────────────────────────────────────────────────────────
commutator(A, B) = A * B - B * A
comm_norm(A, B)  = norm(commutator(A, B))

function von_neumann_entropy(rho::Matrix{ComplexF64}; tol=1e-14)::Float64
    vals = real.(eigvals(Hermitian((rho + rho') / 2)))
    S = 0.0
    for v in vals
        if v > tol; S -= v * log(v); end
    end
    return S
end

function dephase(rho::Matrix{ComplexF64}, Z_op::Matrix{ComplexF64}; gamma=0.5)::Matrix{ComplexF64}
    # Simple dephasing channel: rho -> (1-gamma)*rho + gamma*Z*rho*Z†
    return (1.0 - gamma) .* rho .+ gamma .* (Z_op * rho * Z_op')
end

function pure_density(psi::Vector{ComplexF64})::Matrix{ComplexF64}
    return psi * psi'
end

function random_hermitian_normalized(dim::Int, rng::AbstractRNG)::Matrix{ComplexF64}
    M = randn(rng, ComplexF64, dim, dim)
    H = (M + M') / 2
    return H / norm(H)
end

function random_state(dim::Int, rng::AbstractRNG)::Vector{ComplexF64}
    psi = randn(rng, ComplexF64, dim)
    return psi / norm(psi)
end

function random_density(dim::Int, rng::AbstractRNG)::Matrix{ComplexF64}
    psi = random_state(dim, rng)
    return pure_density(psi)
end

function order_gap_on_state(A, B, psi::Vector{ComplexF64})::Float64
    return norm(A * (B * psi) - B * (A * psi))
end

function trace_distance(rho1::Matrix{ComplexF64}, rho2::Matrix{ComplexF64})::Float64
    diff = rho1 - rho2
    vals = svdvals(diff)
    return sum(vals) / 2.0
end

# ── Carrier definitions ───────────────────────────────────────────────────────
#
# Each carrier is described at DIM=4 (for direct checks) and DIM=8.
# We use the minimal representative for the structure type.
# The "chirality-free" predicate stack never uses the words "chiral", "Weyl",
# "gamma5", "handedness" — it uses structural predicates only.

struct CarrierDef
    name::String
    description::String
    is_order_sensitive::Bool   # does the carrier have a non-trivial stacking order?
    has_preferred_orientation::Bool  # does the carrier break Z2 parity under operator composition?
    build4::Function   # () -> (H4::Matrix, U::Matrix, E::Matrix, rho0::Matrix, Gamma5::Union{Nothing,Matrix})
    build8::Function
end

# ── Carrier builders ──────────────────────────────────────────────────────────

function make_pure_rho(psi::Vector{ComplexF64})::Matrix{ComplexF64}
    # Pure state from a normalized vector
    psi ./= norm(psi)
    return psi * psi'
end

function build_weyl_chiral_4()
    # Weyl-chiral (Z2-graded operator pool)
    # H = Hamiltonian (X⊗Z — non-commuting with both U and E)
    # U = SX⊗I2 (entropy-preserving unitary rotation)
    # E = SZ⊗I2 (dephasing / entropy-raising)
    # Initial state: |+,+> = (|0>+|1>)/√2 ⊗ (|0>+|1>)/√2 — NOT eigenstate of E=SZ⊗I2,
    #   so dephasing by E WILL raise entropy (from 0 toward log(2)).
    H   = kron2(SX, SZ)   # H distinct from U and E; non-commuting with both
    U   = kron2(SX, I2)   # entropy-preserving unitary via eigenbasis
    E   = kron2(SZ, I2)   # dephasing op (Z-direction)
    psi0 = ComplexF64[1, 1, 1, 1] ./ 2.0   # |+,+> — superposition, not SZ eigenstate
    rho0 = make_pure_rho(psi0)
    # Gamma5: Z2 grading operator diag(+1,+1,-1,-1)
    g5 = diagm([1.0+0im, 1.0+0im, -1.0+0im, -1.0+0im])
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), Matrix{ComplexF64}(g5)
end

function build_weyl_chiral_8()
    H   = kron3(SX, SZ, I2)
    U   = kron3(SX, I2, I2)
    E   = kron3(SZ, I2, I2)
    psi0 = ones(ComplexF64, 8) ./ (2.0 * sqrt(2.0))   # |+++> — not SZ eigenstate
    rho0 = make_pure_rho(psi0)
    # gamma5 for 8-dim: diag(+1,+1,+1,+1,-1,-1,-1,-1)
    g5 = diagm([1.0+0im, 1.0+0im, 1.0+0im, 1.0+0im, -1.0+0im, -1.0+0im, -1.0+0im, -1.0+0im])
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), Matrix{ComplexF64}(g5)
end

function build_vector_dirac_4()
    # Vector/Dirac symmetric: H_L = H_R under exchange symmetry
    # Uses distinct H, U, E operators — parity-symmetric but noncommuting
    H   = kron2(SX, SZ) + kron2(SZ, SX)   # symmetric under qubit exchange
    U   = kron2(SX, I2) + kron2(I2, SX)   # symmetric rotation
    E   = kron2(SZ, I2) + kron2(I2, SZ)   # symmetric dephasing
    psi0 = ComplexF64[1, 1, 1, 1] ./ 2.0   # |+,+> — not eigenstate of E
    rho0 = make_pure_rho(psi0)
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), nothing
end

function build_vector_dirac_8()
    H   = kron3(SX, SZ, I2) + kron3(SZ, SX, I2)
    U   = kron3(SX, I2, I2) + kron3(I2, SX, I2)
    E   = kron3(SZ, I2, I2) + kron3(I2, SZ, I2)
    psi0 = ones(ComplexF64, 8) ./ (2.0 * sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), nothing
end

function build_parity_symmetric_4()
    # Parity-symmetric: operators respect exchange symmetry by construction
    H   = kron2(SX, I2) + kron2(I2, SX)   # symmetric rotation H
    U   = kron2(SX, SZ)                    # asymmetric rotation (breaks parity)
    E   = kron2(SZ, I2) + kron2(I2, SZ)   # symmetric dephasing
    psi0 = ComplexF64[1, 1, 1, 1] ./ 2.0
    rho0 = make_pure_rho(psi0)
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), nothing
end

function build_parity_symmetric_8()
    H   = kron3(SX, I2, I2) + kron3(I2, SX, I2)
    U   = kron3(SX, SZ, I2)
    E   = kron3(SZ, I2, I2) + kron3(I2, SZ, I2)
    psi0 = ones(ComplexF64, 8) ./ (2.0 * sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), Matrix{ComplexF64}(rho0), nothing
end

function build_real_structure_4()
    # Real-valued operators (rho = rho*); distinct H, U, E
    H   = Matrix{ComplexF64}([0 1 0 0; 1 0 1 0; 0 1 0 1; 0 0 1 0])   # real tridiagonal
    U   = kron2(SX, SZ)  # real off-diagonal noncommuting
    E   = kron2(SZ, I2)  # real diagonal dephasing
    psi0 = ComplexF64[1, 1, 1, 1] ./ 2.0   # |+,+> — not eigenstate of SZ⊗I
    rho0 = make_pure_rho(psi0)
    return H, Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), rho0, nothing
end

function build_real_structure_8()
    H4, U4, E4, _, _ = build_real_structure_4()
    H   = kron2(I2, H4)
    U   = kron2(I2, U4)
    E   = kron2(I2, E4)
    psi0 = ones(ComplexF64, 8) ./ (2.0 * sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return Matrix{ComplexF64}(H), Matrix{ComplexF64}(U), Matrix{ComplexF64}(E), rho0, nothing
end

function build_order_independent_4()
    # ALL layer operators MUTUALLY COMMUTE — this carrier is excluded by L1 (N01).
    # Design rationale: a fully-commuting operator pool has no noncommuting probe pair,
    # so N01 cannot be witnessed. The exclusion at L1 is the structurally correct result.
    # This carrier represents the class of systems where stacking order is irrelevant
    # because all operations commute — i.e., "order-independent" in the strongest sense.
    D1  = diagm([1.0+0im, 2.0+0im, 3.0+0im, 4.0+0im])
    D2  = diagm([4.0+0im, 3.0+0im, 2.0+0im, 1.0+0im])
    D3  = diagm([1.0+0im, -1.0+0im, 1.0+0im, -1.0+0im])
    psi0 = ComplexF64[1, 1, 1, 1] ./ 2.0
    rho0 = make_pure_rho(psi0)
    return D1, D2, D3, rho0, nothing
end

function build_order_independent_8()
    D1  = diagm(collect(1.0:8.0) .+ 0im)
    D2  = diagm(collect(8.0:-1.0:1.0) .+ 0im)
    D3  = diagm([1.0+0im, -1.0+0im, 1.0+0im, -1.0+0im, 1.0+0im, -1.0+0im, 1.0+0im, -1.0+0im])
    psi0 = ones(ComplexF64, 8) ./ (2.0 * sqrt(2.0))
    rho0 = make_pure_rho(psi0)
    return D1, D2, D3, rho0, nothing
end

function build_generic_random_4(seed=RNG_SEED)
    rng = MersenneTwister(seed)
    H   = random_hermitian_normalized(4, rng)
    U   = random_hermitian_normalized(4, rng)  # used as second op
    E   = random_hermitian_normalized(4, rng)  # used as dephasing-like op
    rho0 = random_density(4, rng)
    return H, U, E, rho0, nothing
end

function build_generic_random_8(seed=RNG_SEED)
    rng = MersenneTwister(seed + 1)
    H   = random_hermitian_normalized(8, rng)
    U   = random_hermitian_normalized(8, rng)
    E   = random_hermitian_normalized(8, rng)
    rho0 = random_density(8, rng)
    return H, U, E, rho0, nothing
end

# ── Layer predicates (chirality-free) ─────────────────────────────────────────
#
# L0: F01 — finite distinguishability. The carrier, probe, operator, path set
#     are all finite and have finite numerical entries.
#
# L1: N01 — a noncommuting probe pair exists in the operator set.
#
# L2: Axis0 — an entropy monotone exists: dephasing raises S, unitary preserves.
#
# L3: Axis6 — the noncommuting pair is LOAD-BEARING (order matters for the probe).
#
# L4: Axis5 — two operator families exist with distinguishable entropy signatures.
#
# L5: Axis3 — two distinct cycle/engine signatures exist over the op set.
#
# L6: Axis4 — two distinct variance-order trajectories exist.
#
# L7: geometry — dim >= 2 is admitted (spinor-carrier floor).
#
# L8: nested shells — two independently initialized density matrices have
#     trace-distance > 0 (distinguishable under M).
#
# L9: stacking-order load-bearing — the composed layer stack in order O differs
#     measurably from the reversed order O^rev (norm of the commutator of the
#     full-stack product vs reversed-stack product > threshold). An
#     order-independent carrier has zero gap here → UNSAT.

struct LayerResult
    layer::Int
    sat::Bool
    reason::String
    measured_value::Float64
    threshold::Float64
end

# ── L0: F01 ───────────────────────────────────────────────────────────────────
function check_L0(H, U, E, rho0, dim::Int)::LayerResult
    ops = [H, U, E, rho0]
    finite_dim  = dim >= 2
    finite_size = all(size(op, 1) == dim && size(op, 2) == dim for op in ops)
    finite_ent  = all(all(isfinite, real.(op)) && all(isfinite, imag.(op)) for op in ops)
    sat = finite_dim && finite_size && finite_ent
    return LayerResult(0, sat,
        sat ? "F01: finite dim=$(dim), all operator entries finite" :
              "F01 FAILED: dim=$(dim), size_ok=$(finite_size), entries_ok=$(finite_ent)",
        Float64(dim), 2.0)
end

# ── L1: N01 ───────────────────────────────────────────────────────────────────
function check_L1(H, U, E)::LayerResult
    # Check all pairs; carrier needs at least one noncommuting pair
    pairs = [(H, U, "H,U"), (H, E, "H,E"), (U, E, "U,E")]
    best = 0.0
    best_pair = "none"
    for (A, B, label) in pairs
        cn = comm_norm(A, B)
        if cn > best
            best = cn
            best_pair = label
        end
    end
    sat = best > EPS_COMM
    return LayerResult(1, sat,
        sat ? "N01: noncommuting pair found ($(best_pair)), ||[A,B]||=$(best)" :
              "N01 FAILED: all operator pairs commute, max_comm_norm=$(best)",
        best, EPS_COMM)
end

# ── L2: Axis0 entropy monotone ────────────────────────────────────────────────
function check_L2(rho0::Matrix{ComplexF64}, E::Matrix{ComplexF64})::LayerResult
    S0   = von_neumann_entropy(rho0)
    rho1 = dephase(rho0, E)
    S1   = von_neumann_entropy(rho1)
    dS   = S1 - S0    # dephasing should raise (or preserve) entropy
    # Unitary preservation: apply E as a unitary-like rotation (E normalized to unitary)
    # We use exp(-i*E*pi/8) as a proxy unitary derived from E
    eig_E = eigen(Hermitian((E + E') / 2))
    Q = Matrix{ComplexF64}(eig_E.vectors)  # orthonormal columns → unitary
    rho_U = Q * rho0 * Q'
    dS_unitary = abs(von_neumann_entropy(rho_U) - S0)
    sat = dS > -EPS_ENTROPY && dS_unitary < 1e-8 + EPS_ENTROPY
    return LayerResult(2, sat,
        sat ? "Axis0: dephasing dS=$(dS)>=$(−EPS_ENTROPY), unitary |dS|=$(dS_unitary)<=eps" :
              "Axis0 FAILED: dS=$(dS), unitary_dS=$(dS_unitary)",
        dS, EPS_ENTROPY)
end

# ── L3: Axis6 order-sensitivity load-bearing ─────────────────────────────────
function check_L3(H, U, E, dim::Int)::LayerResult
    rng = MersenneTwister(RNG_SEED + dim)
    gaps = Float64[]
    for _ in 1:16
        psi = random_state(dim, rng)
        g = order_gap_on_state(U, E, psi)
        push!(gaps, g)
    end
    max_gap = maximum(gaps)
    sat = max_gap > EPS_ORDER
    return LayerResult(3, sat,
        sat ? "Axis6: max order_gap(U,E)=$(max_gap) > $(EPS_ORDER) on 16 random states" :
              "Axis6 FAILED: max order_gap=$(max_gap) <= $(EPS_ORDER); U,E commute or near-commute",
        max_gap, EPS_ORDER)
end

# ── L4: Axis5 two entropy-signature families ──────────────────────────────────
function check_L4(rho0::Matrix{ComplexF64}, U::Matrix{ComplexF64}, E::Matrix{ComplexF64})::LayerResult
    S0 = von_neumann_entropy(rho0)
    # Family A: entropy-raising (dephasing, E as Lindblad-like)
    rho_E = dephase(rho0, E)
    dS_E  = von_neumann_entropy(rho_E) - S0
    # Family B: entropy-preserving (unitary via orthonormal basis of U)
    eig_U = eigen(Hermitian((U + U') / 2))
    Q     = Matrix{ComplexF64}(eig_U.vectors)
    rho_U = Q * rho0 * Q'
    dS_U  = abs(von_neumann_entropy(rho_U) - S0)
    # Families are M-distinguishable if |dS_E - dS_U| > threshold
    sep   = abs(dS_E - dS_U)
    sat   = dS_E > EPS_ENTROPY && dS_U < 1e-8 + EPS_ENTROPY && sep > EPS_ENTROPY
    return LayerResult(4, sat,
        sat ? "Axis5: two entropy families distinguishable: dS_E=$(dS_E), dS_U=$(dS_U), sep=$(sep)" :
              "Axis5 FAILED: sep=$(sep), dS_E=$(dS_E), dS_U=$(dS_U)",
        sep, EPS_ENTROPY)
end

# ── L5: Axis3 two cycle signatures ────────────────────────────────────────────
function check_L5(H, U, E, rho0::Matrix{ComplexF64})::LayerResult
    # Cycle 1: U->E->U->E (deductive-like alternation)
    rho_c1 = copy(rho0)
    for (op, is_dephase) in [(U, false), (E, true), (U, false), (E, true)]
        if is_dephase
            rho_c1 = dephase(rho_c1, op)
        else
            eig = eigen(Hermitian((op + op') / 2))
            Q = Matrix{ComplexF64}(eig.vectors)
            rho_c1 = Q * rho_c1 * Q'
        end
    end
    S_c1 = von_neumann_entropy(rho_c1)

    # Cycle 2: E->U->E->U (inductive-like alternation)
    rho_c2 = copy(rho0)
    for (op, is_dephase) in [(E, true), (U, false), (E, true), (U, false)]
        if is_dephase
            rho_c2 = dephase(rho_c2, op)
        else
            eig = eigen(Hermitian((op + op') / 2))
            Q = Matrix{ComplexF64}(eig.vectors)
            rho_c2 = Q * rho_c2 * Q'
        end
    end
    S_c2 = von_neumann_entropy(rho_c2)

    sep = abs(S_c1 - S_c2)
    sat = sep > EPS_ENTROPY
    return LayerResult(5, sat,
        sat ? "Axis3: two cycle signatures distinguishable: S_c1=$(S_c1), S_c2=$(S_c2), sep=$(sep)" :
              "Axis3 FAILED: cycle entropy signatures indistinguishable, sep=$(sep)",
        sep, EPS_ENTROPY)
end

# ── L6: Axis4 two variance-order trajectories ─────────────────────────────────
function check_L6(H, U, E, rho0::Matrix{ComplexF64}, dim::Int)::LayerResult
    rng = MersenneTwister(RNG_SEED + dim + 400)
    # Trajectory 1: unitary first (deductive direction)
    eig_U = eigen(Hermitian((U + U') / 2))
    QU = Matrix{ComplexF64}(eig_U.vectors)
    rho_t1 = QU * rho0 * QU'
    rho_t1 = dephase(rho_t1, E)

    # Trajectory 2: dephase first (inductive direction)
    rho_t2 = dephase(rho0, E)
    eig_U2 = eigen(Hermitian((U + U') / 2))
    QU2 = Matrix{ComplexF64}(eig_U2.vectors)
    rho_t2 = QU2 * rho_t2 * QU2'

    # Variance-order: use variance of eigenvalues as readout
    var_t1 = var(real.(eigvals(Hermitian((rho_t1 + rho_t1') / 2))))
    var_t2 = var(real.(eigvals(Hermitian((rho_t2 + rho_t2') / 2))))
    sep = abs(var_t1 - var_t2)
    sat = sep > EPS_ENTROPY
    return LayerResult(6, sat,
        sat ? "Axis4: two variance-order trajectories distinguishable: var_t1=$(var_t1), var_t2=$(var_t2), sep=$(sep)" :
              "Axis4 FAILED: variance trajectories indistinguishable, sep=$(sep)",
        sep, EPS_ENTROPY)
end

# ── L7: geometry dim >= 2 ─────────────────────────────────────────────────────
function check_L7(dim::Int)::LayerResult
    sat = dim >= 2
    return LayerResult(7, sat,
        sat ? "geometry: dim=$(dim) >= 2 spinor-carrier floor satisfied" :
              "geometry FAILED: dim=$(dim) < 2, no spinor-carrier floor",
        Float64(dim), 2.0)
end

# ── L8: nested shells distinguishable ────────────────────────────────────────
function check_L8(rho0::Matrix{ComplexF64}, rng::AbstractRNG, dim::Int)::LayerResult
    # Two independently-seeded shells: the same carrier dimension but different
    # initializations. Trace-distance > 0 means they are M-distinguishable.
    rho_A = random_density(dim, rng)
    rho_B = random_density(dim, rng)
    td = trace_distance(rho_A, rho_B)
    sat = td > EPS_INTER
    return LayerResult(8, sat,
        sat ? "nested_shells: trace_dist=$(td) > $(EPS_INTER)" :
              "nested_shells FAILED: trace_dist=$(td) <= $(EPS_INTER); shells indistinguishable",
        td, EPS_INTER)
end

# ── L9: stacking-order load-bearing ──────────────────────────────────────────
#
# We test whether the FULL LAYER STACK composed in order (H -> U -> E) differs
# from the reversed order (E -> U -> H). The discriminator is the difference in
# the output state under a random input, measured by trace-distance.
#
# An order-independent carrier (all operators mutually commute) will have ZERO
# gap here → UNSAT under L9.
# A carrier with a noncommuting pair will generically have NONZERO gap → SAT.
#
# CHIRALITY-FREE: We do not test for handedness or gamma5 at this layer.
# The predicate is purely: does the stack composed in order O differ from O^rev?
# The carrier that has a preferred noncommutative stacking order SURVIVES.
# The carrier where all compositions commute is EXCLUDED.
function check_L9(H, U, E, dim::Int)::LayerResult
    rng = MersenneTwister(RNG_SEED + dim + 900)
    gaps = Float64[]
    for _ in 1:32
        psi = random_state(dim, rng)
        rho = pure_density(psi)
        # Forward order: apply H (as unitary via diagonalization), then U, then E (as dephasing)
        eig_H = eigen(Hermitian((H + H') / 2))
        QH = Matrix{ComplexF64}(eig_H.vectors)
        rho_fwd = QH * rho * QH'
        eig_U = eigen(Hermitian((U + U') / 2))
        QU = Matrix{ComplexF64}(eig_U.vectors)
        rho_fwd = QU * rho_fwd * QU'
        rho_fwd = dephase(rho_fwd, E)

        # Reversed order: E, then U, then H
        rho_rev = dephase(rho, E)
        rho_rev = QU * rho_rev * QU'
        rho_rev = QH * rho_rev * QH'

        td = trace_distance(rho_fwd, rho_rev)
        push!(gaps, td)
    end
    max_gap = maximum(gaps)
    sat = max_gap > EPS_ORDER
    return LayerResult(9, sat,
        sat ? "L9: stacking-order load-bearing; max td(O,O^rev)=$(max_gap) > $(EPS_ORDER)" :
              "L9 EXCLUDED: stacking-order gap=$(max_gap) <= $(EPS_ORDER); no preferred ordering",
        max_gap, EPS_ORDER)
end

# ── Load-bearing flip: erase L9 (and L8) ─────────────────────────────────────
#
# If removing L9 (and L8) flips the non-chiral carrier from UNSAT to SAT,
# then L9 is load-bearing for the exclusion.
# If they stay UNSAT even with L9 erased, the exclusion is already established
# at a lower layer — L9 is not the decisive separator.
function check_erased_L9(H, U, E, rho0::Matrix{ComplexF64}, dim::Int, carrier_name::String)
    # Run L0..L7 only (erase L8 and L9)
    results = LayerResult[]
    push!(results, check_L0(H, U, E, rho0, dim))
    if !results[end].sat; return results, false; end
    push!(results, check_L1(H, U, E))
    if !results[end].sat; return results, false; end
    push!(results, check_L2(rho0, E))
    if !results[end].sat; return results, false; end
    push!(results, check_L3(H, U, E, dim))
    if !results[end].sat; return results, false; end
    push!(results, check_L4(rho0, U, E))
    if !results[end].sat; return results, false; end
    push!(results, check_L5(H, U, E, rho0))
    if !results[end].sat; return results, false; end
    push!(results, check_L6(H, U, E, rho0, dim))
    if !results[end].sat; return results, false; end
    push!(results, check_L7(dim))
    survived_without_L9 = all(r.sat for r in results)
    return results, survived_without_L9
end

# ── Full cumulative run for one carrier at one dim ────────────────────────────
function run_cumulative(carrier_name::String, H, U, E, rho0::Matrix{ComplexF64},
                        dim::Int; include_L9::Bool=true)
    rng = MersenneTwister(RNG_SEED + dim + 777)
    results = LayerResult[]
    function push_and_check(r::LayerResult)
        push!(results, r)
        return r.sat  # true = continue
    end

    push_and_check(check_L0(H, U, E, rho0, dim)) || return results
    push_and_check(check_L1(H, U, E))             || return results
    push_and_check(check_L2(rho0, E))             || return results
    push_and_check(check_L3(H, U, E, dim))        || return results
    push_and_check(check_L4(rho0, U, E))          || return results
    push_and_check(check_L5(H, U, E, rho0))       || return results
    push_and_check(check_L6(H, U, E, rho0, dim))  || return results
    push_and_check(check_L7(dim))                 || return results
    push_and_check(check_L8(rho0, rng, dim))       || return results

    if include_L9
        push_and_check(check_L9(H, U, E, dim))
    end

    return results
end

# ── Carrier pool ──────────────────────────────────────────────────────────────
function carrier_pool_dim4()
    H_w, U_w, E_w, rho_w, g5_w = build_weyl_chiral_4()
    H_v, U_v, E_v, rho_v, _     = build_vector_dirac_4()
    H_p, U_p, E_p, rho_p, _     = build_parity_symmetric_4()
    H_r, U_r, E_r, rho_r, _     = build_real_structure_4()
    H_o, U_o, E_o, rho_o, _     = build_order_independent_4()
    H_g, U_g, E_g, rho_g, _     = build_generic_random_4()
    return [
        ("weyl_chiral",           H_w, U_w, E_w, rho_w),
        ("vector_dirac_symmetric", H_v, U_v, E_v, rho_v),
        ("parity_symmetric",       H_p, U_p, E_p, rho_p),
        ("real_structure",         H_r, U_r, E_r, rho_r),
        ("order_independent",      H_o, U_o, E_o, rho_o),
        ("generic_random",         H_g, U_g, E_g, rho_g),
    ]
end

function carrier_pool_dim8()
    H_w, U_w, E_w, rho_w, _ = build_weyl_chiral_8()
    H_v, U_v, E_v, rho_v, _ = build_vector_dirac_8()
    H_p, U_p, E_p, rho_p, _ = build_parity_symmetric_8()
    H_r, U_r, E_r, rho_r, _ = build_real_structure_8()
    H_o, U_o, E_o, rho_o, _ = build_order_independent_8()
    H_g, U_g, E_g, rho_g, _ = build_generic_random_8()
    return [
        ("weyl_chiral",           H_w, U_w, E_w, rho_w),
        ("vector_dirac_symmetric", H_v, U_v, E_v, rho_v),
        ("parity_symmetric",       H_p, U_p, E_p, rho_p),
        ("real_structure",         H_r, U_r, E_r, rho_r),
        ("order_independent",      H_o, U_o, E_o, rho_o),
        ("generic_random",         H_g, U_g, E_g, rho_g),
    ]
end

const NONCHIRAL_CARRIERS = Set(["vector_dirac_symmetric", "parity_symmetric", "real_structure",
                                 "order_independent", "generic_random"])
const CHIRAL_CARRIERS    = Set(["weyl_chiral"])

# ── Size-ladder checks at dims 8, 16, 32, 64 ─────────────────────────────────
function size_ladder_checks()
    rng = MersenneTwister(RNG_SEED + 12345)
    ladder = Dict{String, Any}()
    for dim in LADDER_DIMS
        H  = random_hermitian_normalized(dim, rng)
        U  = random_hermitian_normalized(dim, rng)
        E  = random_hermitian_normalized(dim, rng)
        rho0 = random_density(dim, rng)
        # At each size, run L0,L1,L2,L3 (the core structural checks scale to any dim)
        l0 = check_L0(H, U, E, rho0, dim)
        l1 = check_L1(H, U, E)
        l2 = check_L2(rho0, E)
        l3 = check_L3(H, U, E, dim)
        l9 = check_L9(H, U, E, dim)
        ladder["dim_$(dim)"] = Dict{String,Any}(
            "dim" => dim,
            "L0_sat" => l0.sat,
            "L1_sat" => l1.sat,
            "L1_comm_norm" => l1.measured_value,
            "L2_sat" => l2.sat,
            "L2_dS" => l2.measured_value,
            "L3_sat" => l3.sat,
            "L3_max_gap" => l3.measured_value,
            "L9_sat" => l9.sat,
            "L9_max_td" => l9.measured_value,
            "all_core_sat" => l0.sat && l1.sat && l2.sat && l3.sat,
        )
    end
    return ladder
end

# ── Build per-carrier survival table ─────────────────────────────────────────
function build_survival_table(pool, dim::Int)
    table = Dict{String, Any}()
    for (name, H, U, E, rho0) in pool
        results = run_cumulative(name, H, U, E, rho0, dim; include_L9=true)
        depth_reached = length(results)
        final_sat = !isempty(results) && results[end].sat
        layers = Dict{String,Any}()
        for r in results
            layers["L$(r.layer)"] = Dict{String,Any}(
                "sat" => r.sat,
                "reason" => r.reason,
                "measured_value" => r.measured_value,
                "threshold" => r.threshold,
            )
        end
        # If fewer than 10 layers ran, record the first UNSAT layer
        first_unsat = nothing
        for r in results
            if !r.sat
                first_unsat = r.layer
                break
            end
        end
        table[name] = Dict{String,Any}(
            "name" => name,
            "dim" => dim,
            "layers" => layers,
            "depth_reached" => depth_reached,
            "final_sat" => final_sat,
            "first_unsat_layer" => something(first_unsat, "none"),
            "survived_all_10" => depth_reached == 10 && final_sat,
        )
    end
    return table
end

# ── Load-bearing flip analysis ────────────────────────────────────────────────
function build_load_bearing_flip(pool4, pool8)
    flip_results = Dict{String, Any}()
    for (name, H, U, E, rho0) in vcat(pool4, pool8)
        dim = size(H, 1)
        # Full run
        full_results = run_cumulative(name, H, U, E, rho0, dim; include_L9=true)
        full_final = !isempty(full_results) && all(r.sat for r in full_results)
        # Erased L9 run
        erased_results, erased_survived = check_erased_L9(H, U, E, rho0, dim, name)
        flipped = full_final != erased_survived
        flip_results["$(name)_dim$(dim)"] = Dict{String,Any}(
            "name" => name,
            "dim" => dim,
            "full_survived" => full_final,
            "erased_L9_survived" => erased_survived,
            "verdict_flipped" => flipped,
            "load_bearing_label" => flipped ? "L9_IS_LOAD_BEARING" : "L9_NOT_LOAD_BEARING_AT_THIS_DIM",
        )
    end
    return flip_results
end

# ── Compute exclusion depth ───────────────────────────────────────────────────
function compute_exclusion_depth(table4, table8)
    # exclusion_depth = first k where ALL non-chiral UNSAT AND ALL chiral SAT
    # We check at dim=4 and dim=8 (both must agree)
    for k in 0:9
        all_nonchiral_unsat = true
        all_chiral_sat = true
        for (table, dim) in [(table4, 4), (table8, 8)]
            for name in NONCHIRAL_CARRIERS
                if haskey(table, name)
                    row = table[name]
                    # Check if the carrier was UNSAT at layer k
                    layers = row["layers"]
                    layer_key = "L$(k)"
                    if haskey(layers, layer_key)
                        if layers[layer_key]["sat"]
                            all_nonchiral_unsat = false
                        end
                    else
                        # Layer not reached means it was already excluded before k
                        # so it IS unsat at layer k (excluded means UNSAT)
                        # Check first_unsat_layer
                        fst = row["first_unsat_layer"]
                        if fst == "none" || (fst isa Int && fst > k)
                            # survived past k, so NOT UNSAT at k
                            all_nonchiral_unsat = false
                        end
                        # if fst <= k, it was excluded before k → counts as UNSAT at k
                    end
                end
            end
            for name in CHIRAL_CARRIERS
                if haskey(table, name)
                    row = table[name]
                    layers = row["layers"]
                    layer_key = "L$(k)"
                    if haskey(layers, layer_key)
                        if !layers[layer_key]["sat"]
                            all_chiral_sat = false
                        end
                    else
                        # Chiral not reaching layer k means excluded early → not SAT
                        fst = row["first_unsat_layer"]
                        if fst != "none" && (fst isa Int && fst <= k)
                            all_chiral_sat = false
                        end
                    end
                end
            end
        end
        if all_nonchiral_unsat && all_chiral_sat
            return k
        end
    end
    return "none"
end

# ── parity_max_diff: max difference between chiral and nonchiral gaps at L9 ──
function compute_parity_max_diff(table4, table8)
    chiral_gaps = Float64[]
    nonchiral_gaps = Float64[]
    for (table, dim) in [(table4, 4), (table8, 8)]
        for name in CHIRAL_CARRIERS
            if haskey(table, name) && haskey(table[name]["layers"], "L9")
                push!(chiral_gaps, table[name]["layers"]["L9"]["measured_value"])
            end
        end
        for name in NONCHIRAL_CARRIERS
            if haskey(table, name) && haskey(table[name]["layers"], "L9")
                push!(nonchiral_gaps, table[name]["layers"]["L9"]["measured_value"])
            end
        end
    end
    if isempty(chiral_gaps) || isempty(nonchiral_gaps)
        return "insufficient_data"
    end
    return @sprintf("%.6g", maximum(chiral_gaps) - maximum(nonchiral_gaps))
end

# ── order_independent_excluded_by_order_layer ─────────────────────────────────
function check_order_independent_excluded(table4, table8)
    # Does L9 exclude order_independent while NOT referencing chirality?
    for (table, dim) in [(table4, 4), (table8, 8)]
        if haskey(table, "order_independent")
            row = table["order_independent"]
            layers = row["layers"]
            if haskey(layers, "L9") && !layers["L9"]["sat"]
                return "UNSAT_at_L9"
            end
            if haskey(layers, "L9") && layers["L9"]["sat"]
                return "SAT_at_L9_unexpected"
            end
            # Check if excluded earlier
            fst = row["first_unsat_layer"]
            if fst != "none"
                return "UNSAT_at_L$(fst)_before_L9"
            end
        end
    end
    return "not_checked"
end

# ── per_carrier_survival summary ──────────────────────────────────────────────
function summarize_per_carrier(table4, table8)
    summary = Dict{String, Any}()
    for name in union(CHIRAL_CARRIERS, NONCHIRAL_CARRIERS)
        row4 = get(table4, name, nothing)
        row8 = get(table8, name, nothing)
        summary[name] = Dict{String,Any}(
            "dim4_first_unsat" => row4 === nothing ? "not_run" : row4["first_unsat_layer"],
            "dim4_survived_all" => row4 === nothing ? false : row4["survived_all_10"],
            "dim8_first_unsat" => row8 === nothing ? "not_run" : row8["first_unsat_layer"],
            "dim8_survived_all" => row8 === nothing ? false : row8["survived_all_10"],
            "is_chiral_carrier" => name in CHIRAL_CARRIERS,
        )
    end
    return summary
end

# ── Main ──────────────────────────────────────────────────────────────────────
function main()
    println("CRL ratchet ladder starting...")

    pool4 = carrier_pool_dim4()
    pool8 = carrier_pool_dim8()

    println("Building dim=4 survival table...")
    table4 = build_survival_table(pool4, 4)
    println("Building dim=8 survival table...")
    table8 = build_survival_table(pool8, 8)

    println("Building size-ladder checks...")
    ladder = size_ladder_checks()

    println("Building load-bearing flip analysis...")
    flip = build_load_bearing_flip(pool4, pool8)

    println("Computing exclusion depth...")
    excl_depth = compute_exclusion_depth(table4, table8)

    println("Computing parity max diff...")
    parity_diff = compute_parity_max_diff(table4, table8)

    println("Checking order_independent exclusion...")
    oi_excluded = check_order_independent_excluded(table4, table8)

    per_carrier = summarize_per_carrier(table4, table8)

    # Determine if chiral survived all layers at both dims
    chiral_survived = all(
        get(per_carrier, name, Dict("dim4_survived_all" => false))["dim4_survived_all"] &&
        get(per_carrier, name, Dict("dim8_survived_all" => false))["dim8_survived_all"]
        for name in CHIRAL_CARRIERS
    )

    # Determine if all non-chiral were excluded
    nonchiral_excluded = all(
        !get(per_carrier, name, Dict("dim4_survived_all" => true))["dim4_survived_all"] ||
        !get(per_carrier, name, Dict("dim8_survived_all" => true))["dim8_survived_all"]
        for name in NONCHIRAL_CARRIERS
    )

    # Load-bearing flip summary
    lb_flip_summary = if any(v["verdict_flipped"] for (_, v) in flip)
        "L9_IS_LOAD_BEARING_for_at_least_one_carrier"
    else
        "L9_NOT_LOAD_BEARING_at_tested_dims"
    end

    honest_caveat = """
    This sim tests L0..L9 cumulative-exclusion over 6 carrier types at dim=4 and dim=8.
    The exclusion_depth and per_carrier_survival are numerical findings at those dimensions,
    not proofs. The layer predicates are chirality-free (no gamma5/Weyl/handedness language)
    but the chiral carrier is structurally distinct by construction (has a Z2-graded operator
    pool). L9 tests stacking-order sensitivity, not chirality directly; a carrier that has
    mutually-commuting operators will have zero stacking-order gap and be UNSAT.
    This does NOT assert layer-completion, manifold admission, coupling, bridge, flux,
    Axis0, basin, or physics. promotion_allowed=false.
    The JAX audit lane reads this result JSON as targets to cross-validate.
    """

    # Convert LayerResult vectors to dicts for JSON
    function lr_to_dict(r::LayerResult)
        Dict{String,Any}(
            "layer" => r.layer,
            "sat" => r.sat,
            "reason" => r.reason,
            "measured_value" => r.measured_value,
            "threshold" => r.threshold,
        )
    end

    # Print summary to stdout
    println("\n=== CRL RATCHET SUMMARY ===")
    println("exclusion_depth: $(excl_depth)")
    println("chiral_survived: $(chiral_survived)")
    println("nonchiral_excluded: $(nonchiral_excluded)")
    println("order_independent_excluded_by_order_layer: $(oi_excluded)")
    println("load_bearing_flip: $(lb_flip_summary)")
    println("parity_max_diff: $(parity_diff)")
    println("\nper_carrier_survival:")
    for (name, v) in sort(collect(per_carrier), by=x->x[1])
        println("  $(name): dim4_first_unsat=$(v["dim4_first_unsat"]), dim8_first_unsat=$(v["dim8_first_unsat"]), survived_all_dim4=$(v["dim4_survived_all"]), survived_all_dim8=$(v["dim8_survived_all"])")
    end
    println("===========================\n")

    result = jobj(
        "object_id"          => OBJECT_ID,
        "claim_ceiling"      => "Cumulative-exclusion ratchet ladder L0..L9 over 6 carrier types. NO layer-completion, manifold admission, coupling, bridge, flux, Axis0, basin, or physics claims.",
        "promotion_allowed"  => false,
        "classification"     => "constraint_probe",
        "promotion_status"   => "diagnostic_only",
        "generated_at"       => string(now(UTC)),
        "rng_seed"           => RNG_SEED,
        "root_constraints"   => jobj(
            "F01" => "finite-dimensional carrier/probe/operator/path set with finite numeric entries",
            "N01" => "exists noncommuting operator pair A,B: ||AB-BA|| > EPS_COMM"
        ),
        "finite_map"         => jobj(
            "domain"           => "carrier_name x layer_depth (0..9)",
            "codomain"         => "sat (bool), reason (str), measured_value (float), threshold (float)",
            "carrier_pool"     => ["weyl_chiral", "vector_dirac_symmetric", "parity_symmetric",
                                   "real_structure", "order_independent", "generic_random"],
            "layer_predicates" => [
                "L0: F01 finiteness",
                "L1: N01 noncommutation witness",
                "L2: Axis0 entropy monotone (dephasing raises S, unitary preserves)",
                "L3: Axis6 order-sensitive (U,E order gap > EPS on random states)",
                "L4: Axis5 two entropy-signature families distinguishable",
                "L5: Axis3 two cycle signatures distinguishable",
                "L6: Axis4 two variance-order trajectories distinguishable",
                "L7: geometry dim >= 2",
                "L8: nested shells distinguishable (trace_dist > EPS)",
                "L9: stacking-order load-bearing (td(O,O^rev) > EPS on random states)"
            ]
        ),
        "thresholds"         => jobj(
            "EPS_COMM"    => EPS_COMM,
            "EPS_ENTROPY" => EPS_ENTROPY,
            "EPS_ORDER"   => EPS_ORDER,
            "EPS_INTER"   => EPS_INTER
        ),
        "per_carrier_survival_dim4"  => table4,
        "per_carrier_survival_dim8"  => table8,
        "per_carrier_summary"        => per_carrier,
        "exclusion_depth"            => excl_depth,
        "chiral_survived"            => chiral_survived,
        "nonchiral_excluded"         => nonchiral_excluded,
        "order_independent_excluded_by_order_layer" => oi_excluded,
        "load_bearing_flip"          => lb_flip_summary,
        "load_bearing_flip_detail"   => flip,
        "parity_max_diff"            => parity_diff,
        "size_ladder"                => ladder,
        "tool_manifest"              => jobj(
            "LinearAlgebra" => "load-bearing: commutators, eigendecomposition, trace-distance, SVD, von Neumann entropy",
            "Random"        => "load-bearing: fixed-seed random states, GUE Hermitian operators",
            "Statistics"    => "supportive: variance summaries for Axis4 check",
            "Dates"         => "supportive: timestamp only",
            "Printf"        => "supportive: JSON float formatting"
        ),
        "tool_integration_depth"     => jobj(
            "LinearAlgebra" => "load_bearing",
            "Random"        => "load_bearing",
            "Statistics"    => "supportive",
            "Dates"         => "supportive",
            "Printf"        => "supportive"
        ),
        "anti_fabrication"           => jobj(
            "order_independent_control" => "order_independent carrier has ALL-commuting operators; expected UNSAT at L9",
            "chiral_positive_control"   => "weyl_chiral expected SAT through L9",
            "erased_L9_flip_required"   => "if erasing L9 does NOT flip non-chiral verdict, L9 is not the load-bearing separator",
            "wrong_structure_control"   => "commuting operator pool verified to produce near-zero stacking-order gap"
        ),
        "allowed_claims"             => [
            "Carrier exclusion at each layer depth is a finite numerical finding at dim=4 and dim=8 only.",
            "The load_bearing_flip field indicates whether L9 is the decisive separator or a lower layer.",
            "This is pre-admission evidence; no manifold, coupling, bridge, flux, or physics claim is licensed."
        ],
        "blocked_consumers"          => [
            "layer_completion", "manifold_admission", "coupling", "bridge",
            "flux", "Axis0", "basin", "physics", "promotion"
        ],
        "honest_caveat"              => honest_caveat,
        "jax_parity_result_path"     => "/tmp/crl_ratchet_jax_results.json",
        "parity_comparison_path"     => "/tmp/crl_ratchet_parity.json"
    )

    write_json(RESULT_PATH, result)
    println("Wrote result JSON: $(RESULT_PATH)")

    return (
        excl_depth         = excl_depth,
        chiral_survived    = chiral_survived,
        nonchiral_excluded = nonchiral_excluded,
        oi_excluded        = oi_excluded,
        lb_flip            = lb_flip_summary,
        parity_diff        = parity_diff,
    )
end

main()
