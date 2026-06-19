#!/usr/bin/env julia

using Nemo
using Hecke
using SHA
using Dates

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s10_g2_family_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_nemo_hecke.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_nemo_hecke_results.json")
const CLASSIFICATION = "tool_lego_fit_probe"

json_sha(path::String) = bytes2hex(open(SHA.sha256, path))

function json_escape(s)
    t = replace(String(s), "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n", "\r" => "\\r", "\t" => "\\t")
    return "\"" * t * "\""
end

function to_json(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa AbstractString || x isa Symbol
        return json_escape(x)
    elseif x isa Integer || x isa AbstractFloat
        return string(x)
    elseif x isa Pair
        return to_json(Dict(string(x.first) => x.second))
    elseif x isa AbstractDict
        parts = String[]
        for k in sort(collect(keys(x)); by=string)
            push!(parts, json_escape(string(k)) * ":" * to_json(x[k]))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa Tuple
        return "[" * join([to_json(v) for v in x], ",") * "]"
    elseif x isa AbstractVector
        return "[" * join([to_json(v) for v in x], ",") * "]"
    else
        return json_escape(string(x))
    end
end

function run_counts()
    f = Nemo.GF(7)
    els = collect(f)
    classes = Set{NTuple{4, Int}}()
    borel = Set{NTuple{4, Int}}()
    unipotent = Set{NTuple{4, Int}}()
    toint(x) = Int(Nemo.lift(Nemo.ZZ, x))
    canon(tup) = min(tup, ntuple(i -> mod(-tup[i], 7), 4))
    sl_count = 0
    for a in els, b in els, c in els, d in els
        if a * d - b * c == f(1)
            sl_count += 1
            tup = (toint(a), toint(b), toint(c), toint(d))
            ct = canon(tup)
            push!(classes, ct)
            if toint(c) == 0
                push!(borel, ct)
            end
            if toint(a) == 1 && toint(c) == 0 && toint(d) == 1
                push!(unipotent, ct)
            end
        end
    end
    return Dict(
        "route" => "Nemo GF(7) finite-field matrices; Hecke imported under isolated optional project",
        "sl2_7_order" => sl_count,
        "psl2_7_order" => length(classes),
        "borel_stabilizer_order_in_psl" => length(borel),
        "unipotent_order_in_psl" => length(unipotent),
        "subgroup_chain_orders" => [length(classes), length(borel), length(unipotent), 1],
        "dimension_chain_su3_in_g2" => Dict("su2" => 3, "su3" => 8, "g2" => 14, "g2_minus_su3" => 6),
        "pass" => sl_count == 336 && length(classes) == 168 && length(borel) == 21 && length(unipotent) == 7,
    )
end

function build_result()
    counts = run_counts()
    return Dict(
        "schema_version" => "geo_s10_g2_family_nemo_hecke_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => "system_v6/sims/$(SIM_ID)/$(SIM_ID)_nemo_hecke.jl",
        "source_sha256" => json_sha(SOURCE_PATH),
        "result_path" => "system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_nemo_hecke_results.json",
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => string(Base.active_project()),
            "load_path" => join(Base.LOAD_PATH, ":"),
            "required_project" => joinpath(ROOT, "system_v6", "optional", "nemo_hecke", "Project.toml"),
        ),
        "packages_used" => ["Nemo", "Hecke", "SHA"],
        "claim_path_tools" => ["Nemo"],
        "TOOL_MANIFEST" => Dict(
            "Nemo" => Dict("tried" => true, "used" => true, "reason" => "load-bearing GF(7) matrix enumeration for SL/PSL and subgroup counts"),
            "Hecke" => Dict("tried" => true, "used" => true, "reason" => "supportive optional project import for the S10 finite-group route"),
            "julia_stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization and hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Nemo" => "load_bearing", "Hecke" => "supportive", "julia_stdlib" => "supportive"),
        "tool_calls" => [
            Dict(
                "tool" => "Nemo",
                "qualified_api/function" => "Nemo.GF/lift",
                "input_object" => "all 2x2 matrices over GF(7)",
                "output_object" => counts,
                "positive_case" => "SL(2,7)=336 and PSL(2,7)=168",
                "negative/erased_control" => "quotient by +/-I changes 336 to 168",
                "boundary_case" => "finite sanity row only, not compact/split Lie-form proof",
                "demotion_condition" => "if finite-field enumeration is removed, PSL row is receipt echo",
                "gates" => ["finite_counts", "all_pass"],
            ),
        ],
        "probe_result" => counts,
        "all_pass" => counts["pass"] == true && CLASSIFICATION == "tool_lego_fit_probe",
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        write(io, to_json(payload))
        write(io, "\n")
    end
    println(to_json(Dict("ok" => payload["all_pass"], "mode" => "nemo_hecke", "result_path" => RESULT_PATH)))
    return payload["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
