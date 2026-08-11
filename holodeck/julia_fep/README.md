# holodeck/julia_fep

Isolated Julia environment for the FEP / active-inference stack.

Lives HERE, not in `sim_engines/`, because its dependency chain conflicts with
the main depot: ActiveInference -> ActionModels -> Turing, against the Zygote /
Lux / Enzyme versions the shared environment already pins. It is a separate
heavy layer for the world-model work, not part of CB heavy.

| package | version | state |
|---|---|---|
| ActiveInference.jl | 0.1.2 | loads, performs a real belief update |

Pins: `Distributions` held at 0.25.113. Above that, its `@check_args` macro API
change breaks DistributionsAD, which breaks ActionModels precompilation, which
breaks ActiveInference.

Verified 2026-08-08: A = [0.9 0.1; 0.1 0.9], one observation -> posterior
[0.75, 0.25], sum 1.0, favouring the observed state.

Run it with the project flag or it will resolve against the main depot and fail:

    julia --project=holodeck/julia_fep -e 'using ActiveInference'
