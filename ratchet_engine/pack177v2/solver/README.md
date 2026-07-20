# Solver replay

`run_z3_anf_census.py` asks Z3 for every Boolean ANF coefficient model and
blocks each model after extraction. It compares the exact survivor masks with
the r6 enumeration.

`generate_cvc5_instances.py` writes one frozen SMT-LIB instance per anonymous
source. `run_cvc5_instances.py` executes cvc5 and receipts its SAT/UNSAT
result. A source with at least one deterministic completion must be SAT; a
same-context plural-outcome source must be UNSAT.

These are independent exclusion checks, not mathematical authorities and not
substitutes for the explicit finite census.

