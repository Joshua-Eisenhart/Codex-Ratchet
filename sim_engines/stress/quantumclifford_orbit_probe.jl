# UNOFFICIAL STRESS PROBE (julia leg) — QuantumClifford 2-qubit stabilizer-state enumeration.
#
# classification: unofficial_stress_probe · promotion_allowed: false
# claim_ceiling: capability demonstration only — parks by definition.
#
# Enumerates ALL n-qubit stabilizer states (n=1 negative control, n=2 target)
# exhaustively: every set of n pairwise-commuting, GF(2)-independent signed
# Pauli generators (real phases only), canonicalized to a unique stabilizer
# tableau via QuantumClifford.canonicalize!. The tableau algebra (comm, phase
# tracking, canonical rref) is group-theoretic work QuantumOptics/jnp lack.
#
# Emits one JSON line on stdout (the last line starting with "{").

using QuantumClifford
using JSON

const CHARS = ('I', 'X', 'Y', 'Z')
# char -> (xbit, zbit) in the QuantumClifford tableau convention
const XZ = Dict('I' => (false, false), 'X' => (true, false),
                'Y' => (true, true), 'Z' => (false, true))

"All non-identity Pauli bit-patterns on n qubits (4^n - 1 of them)."
function pauli_patterns(n::Int)
    pats = Vector{Tuple{Vector{Bool},Vector{Bool}}}()
    for idx in 0:(4^n - 1)
        xs = Bool[]; zs = Bool[]; v = idx
        for _ in 1:n
            c = CHARS[(v % 4) + 1]
            push!(xs, XZ[c][1]); push!(zs, XZ[c][2])
            v ÷= 4
        end
        any(xs) || any(zs) || continue   # skip identity
        push!(pats, (xs, zs))
    end
    return pats
end

"All signed (real-phase) non-identity Pauli operators on n qubits."
function signed_paulis(n::Int)
    ops = PauliOperator[]
    for (xs, zs) in pauli_patterns(n), ph in (0x0, 0x2)   # + and -
        push!(ops, PauliOperator(ph, xs, zs))
    end
    return ops
end

pattern_bits(p::PauliOperator) = (collect(xbit(p)), collect(zbit(p)))

"Exhaustive stabilizer-state enumeration for n in {1,2} via canonical tableaux."
function enumerate_states(n::Int)
    ops = signed_paulis(n)
    seen = Dict{String,Stabilizer}()
    rejected_anticommuting = 0
    rejected_dependent = 0
    considered = 0
    if n == 1
        for p in ops
            considered += 1
            s = canonicalize!(Stabilizer([p]))
            seen[string(s)] = s
        end
    elseif n == 2
        for i in 1:length(ops), j in (i+1):length(ops)
            considered += 1
            p1, p2 = ops[i], ops[j]
            if pattern_bits(p1) == pattern_bits(p2)      # ±same pattern: dependent
                rejected_dependent += 1
                continue
            end
            if comm(p1, p2) != 0x0                       # anticommuting: excluded
                rejected_anticommuting += 1
                continue
            end
            s = canonicalize!(Stabilizer([p1, p2]))
            seen[string(s)] = s
        end
    else
        error("probe scoped to n in {1,2}")
    end
    return seen, considered, rejected_anticommuting, rejected_dependent
end

"Verify one canonical stabilizer state with QuantumClifford primitives."
function verify_state(s::Stabilizer, n::Int)
    rows = [s[i] for i in 1:length(s)]
    rows_commute = all(comm(rows[i], rows[j]) == 0x0
                       for i in 1:length(rows) for j in (i+1):length(rows))
    phases_real = all(r.phase[] in (0x0, 0x2) for r in rows)
    nonzero_rows = count(r -> any(collect(xbit(r))) || any(collect(zbit(r))), rows)
    # GF(2) independence for n<=2: nonzero rows with distinct patterns
    independent = nonzero_rows == n &&
        length(Set(pattern_bits(r) for r in rows)) == length(rows)
    canonical_fixed = string(canonicalize!(copy(s))) == string(s)
    weights = [count(k -> collect(xbit(r))[k] || collect(zbit(r))[k], 1:n) for r in rows]
    return Dict(
        "state" => replace(string(s), "\n" => " | "),
        "rows_commute" => rows_commute,
        "phases_real" => phases_real,
        "independent_full_rank" => independent,
        "canonical_fixed_point" => canonical_fixed,
        "weights" => weights,
        "valid" => rows_commute && phases_real && independent && canonical_fixed,
    )
end

function main()
    t0 = time()
    out = Dict{String,Any}()

    # target: n=2 exhaustive enumeration
    seen2, considered2, anti2, dep2 = enumerate_states(2)
    keys2 = sort(collect(keys(seen2)))
    # sample 10 evenly spaced canonical states for verification
    idxs = round.(Int, range(1, length(keys2), length=min(10, length(keys2))))
    sample = [verify_state(seen2[keys2[i]], 2) for i in unique(idxs)]

    out["n2"] = Dict(
        "unique_count" => length(seen2),
        "pairs_considered" => considered2,
        "rejected_anticommuting" => anti2,
        "rejected_dependent_pattern" => dep2,
        "sample_verified" => sample,
        "sample_all_valid" => all(d["valid"] for d in sample),
    )

    # negative control: same path at n=1 must give 6, not 60
    seen1, considered1, _, _ = enumerate_states(1)
    out["n1"] = Dict("unique_count" => length(seen1),
                     "singles_considered" => considered1)

    # negative control: a genuinely anticommuting pair is excluded by comm
    pxx = PauliOperator(0x0, Bool[true, true], Bool[false, false])   # +XX
    pzi = PauliOperator(0x0, Bool[false, false], Bool[true, false])  # +ZI
    out["anticommuting_pair_control"] = Dict(
        "pair" => "+XX vs +ZI",
        "comm" => Int(comm(pxx, pzi)),
        "excluded" => comm(pxx, pzi) != 0x0,
    )

    out["quantumclifford_ops"] = ["PauliOperator", "Stabilizer", "comm",
                                  "canonicalize!", "xbit", "zbit", "phase tableau"]
    out["julia_seconds"] = round(time() - t0, digits=3)
    println(JSON.json(out))
end

main()
