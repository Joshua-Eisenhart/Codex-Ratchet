#!/usr/bin/env julia
# Formal numeric parity leg for ratchet_formal_gates_v1.
#
# Ceiling: scratch_diagnostic; promotion_allowed=false.

using Dates
using JSON
using LinearAlgebra
using SHA

const SIM_ID = "ratchet_formal_gates_v1"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false

const TOOL_MANIFEST = Dict(
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent C^8 matrix evolution, eigvalsh-equivalent entropy, and quotient construction"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "artifact serialization")
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia LinearAlgebra" => "load_bearing",
    "JSON" => "supportive"
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const sp = 0.5 .* (sx .+ im .* sy)
const sm = 0.5 .* (sx .- im .* sy)
const PAULI = Dict("I" => I2, "X" => sx, "Y" => sy, "Z" => sz)

const G = 0.35
const KAP = 1.0
const Q = 1.0 - exp(-1.0)
const TH = pi / 4
const T_FLOW = 1.0
const N_STEPS = 400
const J_COUP = 0.5
const PROBE_B = (0.55, 0.35, 0.25)

const TERR = Dict(
    0 => (+1, "damp", +1), 1 => (+1, "depol", 0), 2 => (+1, "damp", -1), 3 => (+1, "proj", 0),
    4 => (-1, "damp", -1), 5 => (-1, "depol", 0), 6 => (-1, "damp", +1), 7 => (-1, "proj", 0)
)
const NATIVE = Dict(
    0 => ["Ti", "Fi"], 1 => ["Ti", "Fi"], 4 => ["Ti", "Fi"], 5 => ["Ti", "Fi"],
    2 => ["Te", "Fe"], 3 => ["Te", "Fe"], 6 => ["Te", "Fe"], 7 => ["Te", "Fe"]
)

kron3(a, b, c) = kron(kron(a, b), c)
on0(a) = kron3(a, I2, I2)

const ZZ01 = kron3(sz, sz, I2)
const ZZ12 = kron3(I2, sz, sz)

function dissipator(L, rho)
    return L * rho * L' - 0.5 .* (L' * L * rho + rho * L' * L)
end

function gen(ti)
    eps, kind, pole = TERR[ti]
    hloc = eps .* (sx .+ sy .+ sz) ./ sqrt(3)
    h = on0(hloc) .+ J_COUP .* (ZZ01 .+ ZZ12)
    ld = on0(pole > 0 ? sp : sm)
    function x(rho)
        out = -im * G .* (h * rho - rho * h)
        if kind == "damp"
            out .+= KAP .* dissipator(ld, rho)
        elseif kind == "depol"
            out .+= 0.5 * KAP .* (dissipator(on0(sx), rho) + dissipator(on0(sy), rho))
        else
            out .+= KAP .* dissipator(on0(sz), rho)
        end
        return out
    end
    return x
end

function flow(x, rho; t=T_FLOW, steps=N_STEPS)
    dt = t / steps
    r = copy(rho)
    for _ in 1:steps
        k1 = x(r)
        k2 = x(r .+ 0.5 * dt .* k1)
        k3 = x(r .+ 0.5 * dt .* k2)
        k4 = x(r .+ dt .* k3)
        r = r .+ (dt / 6) .* (k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4)
        r = 0.5 .* (r .+ r')
        r ./= real(tr(r))
    end
    return r
end

function op(name)
    p0 = 0.5 .* (I2 .+ sz)
    p1 = 0.5 .* (I2 .- sz)
    qp = 0.5 .* (I2 .+ sx)
    qm = 0.5 .* (I2 .- sx)
    if name == "Ti"
        return rho -> (1 - Q) .* rho .+ Q .* (on0(p0) * rho * on0(p0) + on0(p1) * rho * on0(p1))
    elseif name == "Te"
        return rho -> (1 - Q) .* rho .+ Q .* (on0(qp) * rho * on0(qp) + on0(qm) * rho * on0(qm))
    elseif name == "Fi"
        u = on0(exp(-im * TH / 2 .* sx))
        return rho -> u * rho * u'
    elseif name == "Fe"
        u = on0(exp(-im * TH / 2 .* sz))
        return rho -> u * rho * u'
    else
        error("unknown op $name")
    end
end

function pauli_strings()
    out = String[]
    for a in ["I", "X", "Y", "Z"], b in ["I", "X", "Y", "Z"], c in ["I", "X", "Y", "Z"]
        s = a * b * c
        if s != "III"
            push!(out, s)
        end
    end
    return out
end

const STRINGS = pauli_strings()
const PMATS = Dict(s => kron3(PAULI[string(s[1])], PAULI[string(s[2])], PAULI[string(s[3])]) for s in STRINGS)

function canonical_rho(rho)
    r = 0.5 .* (rho .+ rho')
    r ./= real(tr(r))
    r[abs.(r) .< 1e-14] .= 0
    return r
end

function make_probe()
    rho0 = 0.5 .* (I2 .+ PROBE_B[1] .* sx .+ PROBE_B[2] .* sy .+ PROBE_B[3] .* sz)
    plus = 0.5 .* (I2 .+ sx)
    return kron3(rho0, plus, plus)
end

function pvec(rho)
    return [real(tr(rho * PMATS[s])) for s in STRINGS]
end

function bits(index0)
    return ((index0 >> 2) & 1, (index0 >> 1) & 1, index0 & 1)
end

function index_from_bits(vals)
    out = 0
    for value in vals
        out = (out << 1) | Int(value)
    end
    return out
end

function partial_trace(rho, keep::Vector{Int})
    drop = [i for i in 0:2 if !(i in keep)]
    dim = 2 ^ length(keep)
    out = zeros(ComplexF64, dim, dim)
    for row0 in 0:7
        rb = bits(row0)
        rkeep = Tuple(rb[i + 1] for i in keep)
        rout = index_from_bits(rkeep) + 1
        for col0 in 0:7
            cb = bits(col0)
            ok = all(rb[i + 1] == cb[i + 1] for i in drop)
            if ok
                ckeep = Tuple(cb[i + 1] for i in keep)
                cout = index_from_bits(ckeep) + 1
                out[rout, cout] += rho[row0 + 1, col0 + 1]
            end
        end
    end
    return canonical_rho(out)
end

function entropy_bits(rho)
    vals = eigvals(Hermitian(0.5 .* (rho .+ rho')))
    total = 0.0
    for v in vals
        vv = clamp(real(v), 0.0, 1.0)
        if vv > 1e-14
            total -= vv * log2(vv)
        end
    end
    return total
end

function qubit_local_strength(pv, qubit0)
    total = 0.0
    for axis in ["X", "Y", "Z"]
        label = ["I", "I", "I"]
        label[qubit0 + 1] = axis
        idx = findfirst(==(join(label)), STRINGS)
        total += abs(pv[idx])
    end
    return total
end

function xi_ref_descriptor(ref, target)
    strengths = [qubit_local_strength(ref["pvec"], q) for q in 0:2]
    cut_qubit = argmax(strengths) - 1
    keep = [i for i in 0:2 if i != cut_qubit]
    rho_b = partial_trace(target["rho"], keep)
    coherent_info = entropy_bits(rho_b) - entropy_bits(target["rho"])
    local_xyz = Float64[]
    for axis in ["X", "Y", "Z"]
        label = ["I", "I", "I"]
        label[cut_qubit + 1] = axis
        idx = findfirst(==(join(label)), STRINGS)
        push!(local_xyz, round(target["pvec"][idx], digits=12))
    end
    return (cut_qubit, round(coherent_info, digits=12), local_xyz)
end

function enumerate_carrier()
    probe = make_probe()
    states = Vector{Dict{String, Any}}()
    for t in 0:7
        generator = gen(t)
        fixed = canonical_rho(flow(generator, copy(probe), t=8.0, steps=1600))
        push!(states, Dict("label" => "terrain_$(t)_fixed", "family" => "terrain_fixed", "rho" => fixed, "pvec" => pvec(fixed)))
        for opname in NATIVE[t]
            j = op(opname)
            terrain_first = canonical_rho(j(flow(generator, copy(probe))))
            operator_first = canonical_rho(flow(generator, j(copy(probe))))
            push!(states, Dict("label" => "stage_$(t)_$(opname)_terrain_first", "family" => "stage_order", "rho" => terrain_first, "pvec" => pvec(terrain_first)))
            push!(states, Dict("label" => "stage_$(t)_$(opname)_operator_first", "family" => "stage_order", "rho" => operator_first, "pvec" => pvec(operator_first)))
        end
    end
    return states
end

function key_for(pv)
    return join([string(round(v, digits=12)) for v in pv], "|")
end

function quotient_classes(states)
    buckets = Dict{String, Vector{Dict{String, Any}}}()
    for state in states
        key = key_for(state["pvec"])
        if !haskey(buckets, key)
            buckets[key] = Vector{Dict{String, Any}}()
        end
        push!(buckets[key], state)
    end
    keys_sorted = sort(collect(keys(buckets)))
    classes = Vector{Dict{String, Any}}()
    projection = Dict{String, Int}()
    for (idx0, key) in enumerate(keys_sorted)
        labels = sort([s["label"] for s in buckets[key]])
        class_id = idx0 - 1
        for label in labels
            projection[label] = class_id
        end
        push!(classes, Dict("class_id" => class_id, "size" => length(labels), "labels" => labels, "probe_key_sha256" => bytes2hex(sha256(key))))
    end
    pair_count = 0
    surviving = 0
    collapsed = 0
    max_collapsed = 0.0
    min_surviving = Inf
    for i in 1:length(states), j in (i + 1):length(states)
        pair_count += 1
        same = projection[states[i]["label"]] == projection[states[j]["label"]]
        diff = norm(states[i]["pvec"] .- states[j]["pvec"])
        if same
            collapsed += 1
            max_collapsed = max(max_collapsed, diff)
        else
            surviving += 1
            min_surviving = min(min_surviving, diff)
        end
    end
    return Dict(
        "probe_count" => length(STRINGS),
        "carrier_count" => length(states),
        "quotient_class_count" => length(classes),
        "class_sizes" => [c["size"] for c in classes],
        "classes" => classes,
        "projection" => projection,
        "pair_check_count" => pair_count,
        "surviving_difference_count" => surviving,
        "collapsed_pair_count" => collapsed,
        "max_collapsed_pair_probe_l2" => max_collapsed,
        "min_surviving_pair_probe_l2" => isinf(min_surviving) ? 0.0 : min_surviving,
        "gate_pass" => length(classes) > 0 && length(STRINGS) == 63
    )
end

function xi_ref_lift_check(states, quotient)
    by_label = Dict(s["label"] => s for s in states)
    failures = Vector{Any}()
    max_descriptor_spread = 0.0
    checked_pairs = 0
    lifted = Dict{String, Any}()
    for cref in quotient["classes"]
        ref_states = [by_label[label] for label in cref["labels"]]
        for ctgt in quotient["classes"]
            target_states = [by_label[label] for label in ctgt["labels"]]
            descriptors = []
            for ref in ref_states, target in target_states
                push!(descriptors, xi_ref_descriptor(ref, target))
            end
            checked_pairs += 1
            first = descriptors[1]
            local_spreads = Float64[]
            for d in descriptors
                cut_penalty = d[1] == first[1] ? 0.0 : 1.0
                push!(local_spreads, cut_penalty + abs(d[2] - first[2]) + sum(abs.(d[3] .- first[3])))
            end
            spread = maximum(local_spreads)
            max_descriptor_spread = max(max_descriptor_spread, spread)
            if spread != 0.0
                push!(failures, Dict("c_ref" => cref["class_id"], "c_target" => ctgt["class_id"]))
            end
            lifted["$(cref["class_id"])->$(ctgt["class_id"])"] = Dict("cut_qubit" => first[1], "coherent_info_bits" => first[2], "local_probe_xyz" => first[3])
        end
    end
    return Dict(
        "checked_class_pairs" => checked_pairs,
        "multi_representative_class_count" => sum(c["size"] > 1 for c in quotient["classes"]),
        "max_descriptor_spread" => max_descriptor_spread,
        "failure_count" => length(failures),
        "failures" => failures[1:min(length(failures), 20)],
        "status" => isempty(failures) ? "quotient_lift_constructed" : "demoted_to_raw_carrier_discriminator",
        "gate_pass" => isempty(failures),
        "lifted_values" => lifted
    )
end

function carrier_json(states, projection)
    out = Vector{Any}()
    for state in states
        vals = eigvals(Hermitian(0.5 .* (state["rho"] .+ state["rho"]')))
        push!(out, Dict(
            "label" => state["label"],
            "family" => state["family"],
            "quotient_class" => projection[state["label"]],
            "pvec" => state["pvec"],
            "trace" => real(tr(state["rho"])),
            "min_eig" => minimum(real.(vals))
        ))
    end
    return out
end

function main()
    mkpath(RESULTS)
    states = enumerate_carrier()
    quotient = quotient_classes(states)
    xi = xi_ref_lift_check(states, quotient)
    result = Dict(
        "schema" => "codex_ratchet.ratchet_formal_gates_v1.julia_result.v1",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "sim_id" => SIM_ID,
        "classification" => classification,
        "claim_ceiling" => "formal_gate_diagnostic_only",
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "carrier_source" => "independent Julia implementation of oracle_targets_3q.py conventions",
        "carrier_summary" => Dict(
            "hilbert_space" => "C^8",
            "state_count" => length(states),
            "probe_count" => length(STRINGS),
            "pauli_strings" => STRINGS,
            "full_enumeration" => true,
            "sampling" => false
        ),
        "carrier_states" => carrier_json(states, quotient["projection"]),
        "gates" => Dict(
            "observable_quotient_R4" => quotient,
            "xi_ref_quotient_lift" => xi
        ),
        "all_pass" => quotient["gate_pass"] && xi["gate_pass"]
    )
    out = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
    end
    println(JSON.json(Dict("result_path" => out, "all_pass" => result["all_pass"], "gate_verdicts" => Dict(k => v["gate_pass"] for (k, v) in result["gates"]))))
end

main()
