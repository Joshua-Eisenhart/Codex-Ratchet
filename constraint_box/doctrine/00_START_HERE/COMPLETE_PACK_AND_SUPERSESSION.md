# Complete Pack and Supersession Rule

This distribution is self-contained.  A recipient does not need an earlier
Gemini pack, recovery pack, audit zip, ClaimGate patch, or LevOS checkout to
understand or run its implemented core.

## Supersession is narrow

This pack supersedes earlier architecture descriptions only for the
ConstraintBox proposal.  It does not rewrite repository history or owner
decisions.

| Older recurring formulation | Treatment here |
|---|---|
| ClaimGate as receipt-shape verifier | Replaced by controller-owned task profiles and execution |
| ClaimGate as CR-only bridge | Replaced by standalone ConstraintBox plus optional CR/Lev adapters |
| One linear LLM workflow | Replaced by a persistent branch complex |
| LLM calls a gate voluntarily | Replaced by controller-owned execution boundary |
| Full Sim Engines inside lean gate | Rejected; engines remain external workers |
| Julia/PyTorch in lean core | Rejected |
| NumPy absent | Rejected; contained NumPy is optional and useful |
| Every numeric claim requires all engines | Rejected as generic platform rule |
| Similar outputs justify merging | Rejected; continuation-relative evidence is required |
| Low score justifies pruning | Rejected; empty finite fibre or falsifier is required |
| Pi is the architecture | Rejected; agent harness is replaceable |

No older artifact is silently incorporated.  Useful mechanisms have been
restated in the present schemas, runtime, and documents.
