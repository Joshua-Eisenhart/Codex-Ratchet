# External Additions Roadmap

This is a comparison queue, not an install instruction.

| Candidate | Potential value | Main discriminator | Priority |
|---|---|---|---|
| in-toto | binds planned steps to materials/products and functionaries | catches artifact/execution mismatch missed by local receipt | high |
| Cedar | fast capability authorization | clearer/safer than custom policy for real workload | medium |
| TLC | deadlock and illegal transition checking | finds counterexample in controller model | high development |
| Apalache | SMT-backed symbolic TLA+ checking | useful where TLC state explosion dominates | medium |
| cvc5 | alternate solver and proof formats | catches encoding/solver-specific result | medium |
| Hypothesis | generated edge cases and shrinking | finds new minimal hostile fixture | high test |
| JSON Schema 2020-12 | closed object contracts | rejects drift without hand-coded walkers | medium |
| Pi or other harness | model/session/tool loop | demonstrates better containment than direct API adapter | open |
| Gondolin/Docker/OpenShell | OS process containment | prevents filesystem/network capability escape | later |
| agentOS | lightweight V8/WASM capability runtime | resource/security improvement over subprocess profiles | research |
| JAX | batch and GPU checking | bounded task materially exceeds NumPy performance | later |
| Wasmtime/WASI | portable restricted workers | reduces native worker authority | later |

No addition is admitted because it is popular, installed, or conceptually
aligned.  Each needs a task where it detects an error or provides a measured
resource advantage over the current profile.
