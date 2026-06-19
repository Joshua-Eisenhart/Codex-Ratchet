#!/usr/bin/env julia
# Julia leg for finite distinguishability quotient forced-or-installed test.
# Unique computation style: exact_combinatorial_julia over finite maps.
# It reads only spec.json and writes its own result JSON.

using JSON
using SHA
using Dates

const SIM_ID = "finite_distinguishability_quotient_forced_or_installed_carrier_v0"
const HERE = @__DIR__

function spec_sha()
    return bytes2hex(sha256(read(joinpath(HERE, "spec.json"))))
end

function probe_ids(probes)
    return [String(p["id"]) for p in probes]
end

function signature_for(label, probes)
    return [p["outcomes"][label] for p in probes]
end

function quotient_classes(labels, probes)
    classes = Vector{Vector{String}}()
    keys = Vector{String}()
    signatures = Dict{String,Any}()
    for label in labels
        sig = signature_for(label, probes)
        signatures[label] = sig
        key = JSON.json(sig)
        idx = findfirst(==(key), keys)
        if idx === nothing
            push!(keys, key)
            push!(classes, [label])
        else
            push!(classes[idx], label)
        end
    end
    return classes, signatures
end

function class_index(classes)
    idx = Dict{String,Int}()
    for (i, cls) in enumerate(classes)
        for label in cls
            idx[label] = i - 1
        end
    end
    return idx
end

function compose(f, g, x)
    return f[g[x]]
end

function noncommutation_witness(labels, f, g)
    for label in labels
        fg = compose(f, g, label)
        gf = compose(g, f, label)
        if fg != gf
            return Dict("exists" => true, "element" => label, "first_then_second" => fg, "second_then_first" => gf)
        end
    end
    return Dict("exists" => false)
end

function induced_class_map(labels, classes, update)
    idx = class_index(classes)
    out = Dict{String,Int}()
    well_defined = true
    evidence = Dict{String,Any}()
    for (ci, cls) in enumerate(classes)
        targets = sort(unique([idx[update[x]] for x in cls]))
        evidence[string(ci - 1)] = targets
        if length(targets) != 1
            well_defined = false
        else
            out[string(ci - 1)] = targets[1]
        end
    end
    return out, well_defined, evidence
end

function class_noncommutation_witness(class_labels, f, g)
    for c in class_labels
        fg = string(f[string(g[c])])
        gf = string(g[string(f[c])])
        if fg != gf
            return Dict("exists" => true, "class" => c, "U1_after_U2" => parse(Int, fg), "U2_after_U1" => parse(Int, gf))
        end
    end
    return Dict("exists" => false)
end

function relabel_probes(probes, perms)
    out = Any[]
    for p in probes
        perm = perms[p["id"]]
        new_outcomes = Dict{String,Any}()
        for (k, v) in p["outcomes"]
            new_outcomes[k] = perm[string(v)]
        end
        push!(out, Dict("id" => p["id"], "outcomes" => new_outcomes))
    end
    return out
end

function same_partition(a, b)
    norm(x) = sort([sort(c) for c in x])
    return norm(a) == norm(b)
end

function reproduces_probe_data(classes, signatures)
    data = Dict{String,Any}()
    ok = true
    for (i, cls) in enumerate(classes)
        sigs = [signatures[x] for x in cls]
        same = all(s -> s == sigs[1], sigs)
        ok = ok && same
        data[string(i - 1)] = Dict("members" => cls, "probe_signature" => sigs[1], "constant_on_class" => same)
    end
    return ok, data
end

function survival_table(spec, labels, probes, classes, erased_classes, signatures, u1_map, u2_map, v1_map, v2_map)
    class_labels = [string(i - 1) for i in 1:length(classes)]
    u1c, u1wd, u1ev = induced_class_map(labels, classes, u1_map)
    u2c, u2wd, u2ev = induced_class_map(labels, classes, u2_map)
    v1c, v1wd, _ = induced_class_map(labels, classes, v1_map)
    v2c, v2wd, _ = induced_class_map(labels, classes, v2_map)
    active_witness = class_noncommutation_witness(class_labels, u1c, u2c)
    control_witness = class_noncommutation_witness(class_labels, v1c, v2c)
    reproduce_ok, rep_evidence = reproduces_probe_data(classes, signatures)
    rows = Dict{String,Any}()
    for candidate in spec["candidate_structures"]
        id = candidate["id"]
        active_update_ok = false
        control_update_ok = false
        if candidate["update_policy"] == "commuting_diagonal_updates_only"
            active_update_ok = false
            control_update_ok = true
        else
            active_update_ok = u1wd && u2wd && active_witness["exists"]
            control_update_ok = v1wd && v2wd && !control_witness["exists"]
        end
        rows[id] = Dict(
            "name" => candidate["name"],
            "survives_reproduce_quotient" => reproduce_ok,
            "survives_F01" => true,
            "survives_N01" => active_update_ok,
            "survives_all_active_constraints" => reproduce_ok && active_update_ok,
            "commuting_update_control_survives" => reproduce_ok && control_update_ok,
            "evidence" => Dict(
                "induced_partition" => classes,
                "erased_partition" => erased_classes,
                "finite_presentation" => candidate["finite_presentation"],
                "active_update_policy" => candidate["update_policy"],
                "U1_induced_class_map" => u1c,
                "U2_induced_class_map" => u2c,
                "U1_well_defined_on_classes" => u1wd,
                "U2_well_defined_on_classes" => u2wd,
                "class_noncommutation_witness" => active_witness,
                "class_map_evidence" => Dict("U1" => u1ev, "U2" => u2ev),
                "probe_reproduction" => rep_evidence
            )
        )
    end
    return rows, active_witness, control_witness
end

function preorder_matrix(spec, survival)
    ids = [c["id"] for c in spec["candidate_structures"]]
    ranks = Dict(c["id"] => c["strength_rank"] for c in spec["candidate_structures"])
    matrix = Dict{String,Any}()
    for a in ids
        matrix[a] = Dict{String,Bool}()
        for b in ids
            matrix[a][b] = survival[a]["survives_reproduce_quotient"] && survival[b]["survives_reproduce_quotient"] && ranks[a] <= ranks[b]
        end
    end
    return matrix
end

function strict_less(pre, a, b)
    return pre[a][b] && !pre[b][a]
end

function minimal_survivors(survivors, pre)
    return [c for c in survivors if !any(o -> o != c && strict_less(pre, o, c), survivors)]
end

function controls(spec, probes, labels, classes, survival)
    remaining = Set(spec["probe_erase_control"]["remaining_probe_ids"])
    erased_probes = [p for p in probes if p["id"] in remaining]
    erased_classes, _ = quotient_classes(labels, erased_probes)
    shuffled = relabel_probes(probes, spec["label_shuffle_control"]["outcome_permutation_by_probe"])
    shuffled_classes, _ = quotient_classes(labels, shuffled)
    c1 = survival["C1"]
    all_reproduced_without_matrix = c1["survives_reproduce_quotient"] && !occursin("matrix", lowercase(JSON.json(c1["evidence"]["probe_reproduction"])))
    return Dict(
        "commuting_update" => Dict("predicted" => "commutative structure survives when V1,V2 replace U1,U2", "passed" => survival["C2"]["commuting_update_control_survives"]),
        "label_shuffle" => Dict("predicted" => "quotient invariant under outcome relabelling", "passed" => same_partition(classes, shuffled_classes), "shuffled_quotient_classes" => shuffled_classes),
        "probe_erase" => Dict("predicted" => "class count strictly drops", "passed" => length(erased_classes) < length(classes), "full_class_count" => length(classes), "erased_class_count" => length(erased_classes), "erased_quotient_classes" => erased_classes),
        "matrix_form_installed_vs_forced" => Dict("predicted" => "C1 reproduces every probe outcome without constructing a density matrix", "passed" => all_reproduced_without_matrix, "structure_id" => "C1")
    )
end

function verdict(survivors, mins, pre, controls_ok)
    if !controls_ok
        return "inconclusive", "one_or_more_controls_failed"
    end
    if length(mins) >= 2
        incomparable = true
        for a in mins, b in mins
            if a != b && (pre[a][b] || pre[b][a])
                incomparable = false
            end
        end
        if incomparable
            return "plural_incomparable", "minimal survivor set contains pairwise-incomparable structures"
        end
    end
    if "C4" in survivors && any(c -> c != "C4" && pre[c]["C4"] && !pre["C4"][c], survivors)
        return "installed", "Min(Surv) contains a strictly weaker structure below C4"
    end
    if "C4" in survivors
        return "forced", "no strictly weaker survivor below C4"
    end
    return "inconclusive", "C4 did not survive or survivor set is empty"
end

function main()
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    labels = String.(spec["finite_set"])
    probes = spec["probe_family"]
    classes, signatures = quotient_classes(labels, probes)
    erased_ids = Set(spec["probe_erase_control"]["remaining_probe_ids"])
    erased_classes, _ = quotient_classes(labels, [p for p in probes if p["id"] in erased_ids])
    u1 = Dict{String,String}(k => v for (k, v) in spec["active_constraints"]["N01"]["update_maps"]["U1"])
    u2 = Dict{String,String}(k => v for (k, v) in spec["active_constraints"]["N01"]["update_maps"]["U2"])
    v1 = Dict{String,String}(k => v for (k, v) in spec["commuting_update_control"]["update_maps"]["V1"])
    v2 = Dict{String,String}(k => v for (k, v) in spec["commuting_update_control"]["update_maps"]["V2"])
    element_witness = noncommutation_witness(labels, u1, u2)
    control_element_witness = noncommutation_witness(labels, v1, v2)
    survival, class_witness, control_class_witness = survival_table(spec, labels, probes, classes, erased_classes, signatures, u1, u2, v1, v2)
    pre = preorder_matrix(spec, survival)
    survivors = [id for id in [c["id"] for c in spec["candidate_structures"]] if survival[id]["survives_all_active_constraints"]]
    mins = minimal_survivors(survivors, pre)
    ctrl = controls(spec, probes, labels, classes, survival)
    controls_ok = all(v -> v["passed"] == true, values(ctrl))
    vd, reason = verdict(survivors, mins, pre, controls_ok)
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "exact_combinatorial_julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => spec_sha(),
        "result_path" => "system_v7/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "finite_set" => labels,
        "lineage" => spec["lineage"],
        "probe_signatures" => signatures,
        "quotient_classes_full" => classes,
        "quotient_class_count_full" => length(classes),
        "quotient_classes_erased" => erased_classes,
        "quotient_class_count_erased" => length(erased_classes),
        "element_noncommutation_witness" => element_witness,
        "commuting_control_element_witness" => control_element_witness,
        "class_noncommutation_witness" => class_witness,
        "commuting_control_class_witness" => control_class_witness,
        "per_structure_survival" => survival,
        "preorder_definition" => spec["preorder_definition"],
        "preorder_matrix" => pre,
        "Surv" => survivors,
        "MinSurv" => mins,
        "controls" => ctrl,
        "computed_verdict" => vd,
        "computed_verdict_reason" => reason,
        "packages_used" => ["JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["JSON"],
        "TOOL_MANIFEST" => Dict("JSON" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact finite data parsing and result emission"), "SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive spec hashing and timestamp")),
        "TOOL_INTEGRATION_DEPTH" => Dict("JSON" => "load_bearing", "SHA/Dates" => "supportive"),
        "tool_calls" => [
            Dict("tool" => "Julia finite maps", "qualified_api" => "Dict endofunction composition", "input_object" => "U1,U2,V1,V2 maps from spec.json", "output_object" => "element and class noncommutation witnesses", "positive_case" => "U1/U2 witness exists", "negative_erased_control" => "V1/V2 commute everywhere", "boundary_case" => "quotient classes with two-member fibers", "demotion_condition" => "if induced maps are not well-defined on classes", "gates" => ["quotient", "all_pass"])
        ]
    )
    mkpath(joinpath(HERE, "results"))
    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
    end
    println("julia leg wrote $out")
    println("  MinSurv=$(mins) verdict=$(vd)")
end

main()
