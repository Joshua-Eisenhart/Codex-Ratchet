# holodeck/python_fep

Isolated Python environment for the pyhgf side of the FEP stack.

Isolated for the same reason as `holodeck/julia_fep`: it pins old versions that
the main estate has moved past. It is not part of CB heavy.

| | main CB env | this env |
|---|---|---|
| python | 3.13.6 | 3.12.11 |
| jax | 0.10.1 | 0.4.31 |
| pyhgf | 0.1.7 (broken) | 0.3.0 (works) |

pyhgf 0.3.0 requires `jaxlib>=0.4.26,<0.4.32`, and no build in that range has a
python 3.13 wheel. pyhgf 0.2.x caps python at 3.12 outright. So 0.1.7 is the
newest version the main env can hold, and 0.1.7 is broken:
`Network.create_belief_propagation_fn` reads `self.inputs`, which does not exist,
so it builds a network and then cannot ingest data.

Verified 2026-08-08: five observations [0.1 .. 0.5] give an expected_mean
trajectory of [0.0, 0.05, 0.102, 0.154, 0.209] — a real belief update, not a
loaded module.

    holodeck/python_fep/venv/bin/python -c "from pyhgf.model import Network"

## FEP stack, three libraries, three homes

| library | where | why |
|---|---|---|
| pymdp | main CB env | JAX build, no conflict, works as-is |
| pyhgf | here | needs jax 0.4.x and python <=3.12 |
| ActiveInference.jl | holodeck/julia_fep | needs Turing, conflicts with Zygote/Lux/Enzyme |
