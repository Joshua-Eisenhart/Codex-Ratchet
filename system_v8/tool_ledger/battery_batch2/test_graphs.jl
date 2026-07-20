include("common.jl")
using Graphs
b2run("graphs", "system_v8/deep_integration/results/topology/receipt.json") do
    words=[[0,0,0],[0,0,1],[1,1,1]]; g=SimpleGraph(length(words)); for i=1:3,j=i+1:3; sum(words[i].!=words[j])==1 && add_edge!(g,i,j); end
    comps=connected_components(g); n=length(comps); (n,Dict("capacity_words"=>words,"components"=>comps,"rustworkx_receipt_comparison"=>"same Hamming-1 component definition","pass"=>n==2))
end
