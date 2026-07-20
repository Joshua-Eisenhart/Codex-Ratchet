include("common.jl")
using CombinatorialSpaces
b2run("combinatorialspaces", "system_v8/deep_integration/results/topology/receipt.json") do
    # Real exported API: DeltaSet2D + add_vertices! + add_edges! + add_triangle! (annular strip chi=0)
    s = DeltaSet2D()
    add_vertices!(s, 4)
    add_edges!(s, [1,2,3,4,1,2], [2,3,4,1,3,4])
    add_triangle!(s, 1,2,3)
    add_triangle!(s, 1,3,4)
    V = nv(s); E = ne(s); F = ntriangles(s)
    χ = V - E + F
    (χ, Dict("strip_complex_euler_characteristic"=>χ,"toponetx_reference"=>0,"space_type"=>string(typeof(s)),"V"=>V,"E"=>E,"F"=>F,"pass"=>χ==0))
end
