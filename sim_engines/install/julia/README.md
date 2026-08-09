# Julia strict carrier

This environment is portable and independent of whichever Julia project the
user normally activates. It deliberately has no package name/UUID because it
is an environment, not a package with a `src/` module to precompile.

```bash
julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
julia --startup-file=no --project=. -e 'using Graphs, JSON, JSON3, QuantumOptics, Attractors; println("carrier visible")'
```

The project intentionally omits PythonCall, CondaPkg, DLPack, Flux, Lux,
Enzyme, TensorKit, PEPSKit, and ITensorNetworks. Those belong in separate
optional projects until a compatibility and function-level test justifies
adding them.

Installation is not integration. The live doctor can check package visibility;
source and receipt paths in the tool registry determine the declared level.
