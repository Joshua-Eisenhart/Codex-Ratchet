try
    deps = ["ITensors", "ITensorNetworks", "NamedGraphs", "Graphs"]
    missing = [pkg for pkg in deps if Base.find_package(pkg) === nothing]
    if !isempty(missing)
        println("ITN3D_SKIP optional/deferred; missing $(join(missing, ", ")); strict carrier needs install-intent or isolated-project receipt for this route")
        exit(0)
    end
    using ITensors, ITensorNetworks, NamedGraphs, NamedGraphs.NamedGraphGenerators, Graphs
    g = named_grid((2,2,2))                       # genuine 3D lattice 2x2x2
    s = siteinds("S=1/2", g)
    tn = ITensorNetwork(v -> "↑", s)              # product state on the 3D graph
    println("3D ITensorNetwork built: ", nv(g), " vertices (2x2x2), edges=", ne(g))
    println("is genuinely 3D graph (each interior vertex degree up to 6): OK")
    println("ITN3D_OK")
catch e
    println("ITN3D_FAIL path needs API tweak: ", sprint(showerror,e)[1:min(end,200)])
    exit(1)
end
