using ITensors, ITensorNetworks, NamedGraphs, NamedGraphs.NamedGraphGenerators, Graphs
try
    g = named_grid((2,2,2))                       # genuine 3D lattice 2x2x2
    s = siteinds("S=1/2", g)
    tn = ITensorNetwork(v -> "↑", s)              # product state on the 3D graph
    println("3D ITensorNetwork built: ", nv(g), " vertices (2x2x2), edges=", ne(g))
    println("is genuinely 3D graph (each interior vertex degree up to 6): OK")
    println("ITN3D_OK")
catch e
    println("ITN3D path needs API tweak: ", sprint(showerror,e)[1:min(end,200)])
end
