include("common.jl")
using PythonCall, SHA
b2run("pythoncall", "system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json") do
    s=read(joinpath(@__DIR__, "..", "..", "loop3_senses", "results", "senses_v2_slow_memory", "receipt.json"),String); h=bytes2hex(sha256(s)); d=pyimport("json").loads("{\"hash\": \"$h\", \"packet\": \"senses_v2\"}"); back=pyconvert(String, d["hash"]); (back==h,Dict("sha256"=>h,"roundtrip_equal"=>back==h,"pass"=>back==h))
end
