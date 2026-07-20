# Independent engine replay

`run_jax.py`, `run_pytorch.py`, and `run_julia.jl` independently recompute all
256 ANF candidates for every frozen anonymous source in
`receipts/normalized_source_tables.tsv`.

They do not import the stdlib runner's survivor receipt. The only shared input
is the frozen TSV and the declared ANF monomial order.

Expected commands from the pack root:

```text
python3 -B tri-engine/run_jax.py
python3 -B tri-engine/run_pytorch.py
julia --startup-file=no tri-engine/run_julia.jl
python3 -B tri-engine/check_agreement.py
```

The claim path contains no NumPy. Exact equality of survivor masks is required;
numeric tolerance is not applicable.

