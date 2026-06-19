#!/usr/bin/env julia
# Julia leg (authoritative substrate) of the independent survivor-restriction
# noncommutation verification.  This is a FROM-SCRATCH reimplementation in Julia
# of the same math object defined in the spec §5 — it does NOT shell out to the
# Python CORE and does NOT read the JAX/PyTorch results.  If the three engines
# agree, the agreement is genuine (independent code in two languages).
#
# Survivor sets are Julia Sets of Int (0-based cell ids kept 0..N-1 for parity
# with the Python legs).  Constraints are closures (X, H) -> (X', H').  The
# symmetric-difference count is computed via Julia's symdiff.

using JSON3
using SHA
using Dates

const SIM_ID = "independent_survivor_restriction_noncommutation_verify_v0"
const HERE = @__DIR__
const N = 8
const CELLS = Set(0:N-1)

# History: ever-killed set + append order
struct Hist
    ever_killed::Set{Int}
end
Hist() = Hist(Set{Int}())
appendH(H::Hist, killed) = Hist(union(H.ever_killed, Set(killed)))

neighbours(c) = (mod(c - 1, N), mod(c + 1, N))

# history-dependent constraint on a sublattice parity with a neighbour rule
function make_hist_constraint(parity, rule)
    function C(X::Set{Int}, H::Hist)
        killed = Set{Int}()
        for c in sort(collect(X))
            mod(c, 2) == parity || continue
            (lo, hi) = neighbours(c)
            nb_alive = (lo in X ? 1 : 0) + (hi in X ? 1 : 0)
            nb_in_grave = (lo in H.ever_killed) || (hi in H.ever_killed)
            if rule(nb_alive, nb_in_grave)
                push!(killed, c)
            end
        end
        return (setdiff(X, killed), appendH(H, killed))
    end
    return C
end

# amnesic ablation: graveyard read forced false
function make_amnesic_constraint(parity, rule)
    function C(X::Set{Int}, H::Hist)
        killed = Set{Int}()
        for c in sort(collect(X))
            mod(c, 2) == parity || continue
            (lo, hi) = neighbours(c)
            nb_alive = (lo in X ? 1 : 0) + (hi in X ? 1 : 0)
            nb_in_grave = false
            if rule(nb_alive, nb_in_grave)
                push!(killed, c)
            end
        end
        return (setdiff(X, killed), appendH(H, killed))
    end
    return C
end

# extensional (pure per-cell predicate) constraint
function make_extensional_constraint(pred)
    function C(X::Set{Int}, H::Hist)
        killed = Set(c for c in X if !pred(c))
        return (setdiff(X, killed), appendH(H, killed))
    end
    return C
end

# X-reactive static constraint (no history, reads current X neighbourhood)
function make_static_constraint(parity, rule_static)
    function C(X::Set{Int}, H::Hist)
        killed = Set{Int}()
        for c in sort(collect(X))
            mod(c, 2) == parity || continue
            (lo, hi) = neighbours(c)
            nb_alive = (lo in X ? 1 : 0) + (hi in X ? 1 : 0)
            if rule_static(nb_alive)
                push!(killed, c)
            end
        end
        return (setdiff(X, killed), appendH(H, killed))
    end
    return C
end

# rules (mirror the Python core exactly, reimplemented)
rule_hist(nb_alive, g) = (nb_alive >= 1) && g
rule_hist2(nb_alive, g) = (nb_alive == 2) || g
rule_hist_mixed_a(nb_alive, g) = (nb_alive == 0) || ((nb_alive >= 1) && g)
rule_hist_mixed_b(nb_alive, g) = (nb_alive == 0) || g
rule_static(nb_alive) = nb_alive == 2
rule_static2(nb_alive) = nb_alive <= 1

# seed wrapper: kill `seed` cells first inside both orders
function seeded(C, seed)
    function W(X::Set{Int}, H::Hist)
        killed = intersect(Set(seed), X)
        X2 = setdiff(X, killed)
        H2 = appendH(H, killed)
        return C(X2, H2)
    end
    return W
end

function survivor_under_sequence(seq, X0)
    X = Set(X0); H = Hist()
    for C in seq
        (X, H) = C(X, H)
    end
    return X, H
end

function delta_restriction(Ci, Cj, X0)
    Sij, _ = survivor_under_sequence([Ci, Cj], X0)
    Sji, _ = survivor_under_sequence([Cj, Ci], X0)
    return length(symdiff(Sij, Sji))
end

# GNVW index of a uniform ring translation by d sites
function gnvw_index(d)
    perm = [mod(c + d, N) for c in 0:N-1]
    disps = Int[]
    for c in 0:N-1
        dd = mod(perm[c+1] - c, N)
        dd > N ÷ 2 && (dd -= N)
        push!(disps, dd)
    end
    length(Set(disps)) == 1 || return nothing
    return disps[1]
end

function main()
    seed = Set([3])
    X0 = CELLS

    Ci_h = seeded(make_hist_constraint(0, rule_hist), seed)
    Cj_h = seeded(make_hist_constraint(1, rule_hist2), seed)
    Ci_e = seeded(make_extensional_constraint(c -> mod(c, 2) == 0), seed)
    Cj_e = seeded(make_extensional_constraint(c -> c < N ÷ 2), seed)
    Ci_xr = seeded(make_static_constraint(0, rule_static), seed)
    Cj_xr = seeded(make_static_constraint(1, rule_static2), seed)
    Ci_mh = seeded(make_hist_constraint(0, rule_hist_mixed_a), seed)
    Cj_mh = seeded(make_hist_constraint(1, rule_hist_mixed_b), seed)
    Ci_ma = seeded(make_amnesic_constraint(0, rule_hist_mixed_a), seed)
    Cj_ma = seeded(make_amnesic_constraint(1, rule_hist_mixed_b), seed)

    deltas = Dict(
        "delta_history_dependent" => delta_restriction(Ci_h, Cj_h, X0),
        "delta_static_control_extensional" => delta_restriction(Ci_e, Cj_e, X0),
        "delta_static_control_x_reactive" => delta_restriction(Ci_xr, Cj_xr, X0),
        "delta_mixed_history_dependent" => delta_restriction(Ci_mh, Cj_mh, X0),
        "delta_mixed_amnesic" => delta_restriction(Ci_ma, Cj_ma, X0),
    )

    gnvw = Dict(
        "left_shift" => gnvw_index(-1),
        "right_shift" => gnvw_index(1),
        "identity" => gnvw_index(0),
    )

    src = read(@__FILE__, String)
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "native_julia_set_symdiff_and_modular_winding",
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "f01_ancestry" => "root_axioms:53 (finitude) via spec §0",
        "n01_ancestry" => "root_axioms:51 (order as noncommutation) via spec §1.2 R4",
        "generated_at" => Dates.format(now(UTC), "yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => bytes2hex(sha256(src)),
        "result_path" => "system_v7/sims/$SIM_ID/results/$(SIM_ID)_julia_results.json",
        "julia_recomputed_deltas" => deltas,
        "gnvw_index" => gnvw,
        "history_pair_noncommutes" => deltas["delta_history_dependent"] > 0,
        "static_control_extensional_commutes" => deltas["delta_static_control_extensional"] == 0,
        "static_control_x_reactive_commutes" => deltas["delta_static_control_x_reactive"] == 0,
        "mixed_history_pair_noncommutes" => deltas["delta_mixed_history_dependent"] > 0,
        "mixed_amnesic_fully_collapses" => deltas["delta_mixed_amnesic"] == 0,
        "gnvw_signs_flip" => gnvw["left_shift"] !== nothing && gnvw["right_shift"] !== nothing &&
                             gnvw["left_shift"] < 0 < gnvw["right_shift"] && gnvw["identity"] == 0,
        "packages_used" => ["JSON3", "SHA", "Dates"],
        "aligned_packages_load_bearing" => String[],
        "TOOL_MANIFEST" => Dict(
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "result serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "source self-hash"),
        ),
    )

    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do f
        JSON3.pretty(f, result)
    end
    println("julia leg wrote ", out)
    println("  deltas ", deltas)
    println("  gnvw ", gnvw)
end

main()
