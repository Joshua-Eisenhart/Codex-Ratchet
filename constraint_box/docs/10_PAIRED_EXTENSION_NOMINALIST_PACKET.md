# Paired whole-extension nominalist packet

This packet is the first shared carrier for the proposed two-sector extension
work. It is deliberately a finite set-level witness, not a manifold or a
physics implementation. The packet is useful because all three engines receive
the same fixture and must emit the same canonical observation before CB accepts
the external handoff.

## Object and standing fence

The fixture names one finite carrier with an ambient support, a settled support,
newly opened support, binding admits, two operation words, whole completions,
and explicit history-deletion controls. In the intended notation it is an L1
shadow of

\[
  \mathfrak M_r=(\mathcal M^{BO}\leftarrow T_r\to\mathcal M^{OB},\mathcal R_r,H_r),
\]

but no topology, metric, entropy law, chirality, time law, basin, or physical
interpretation is admitted by this packet. `promotion_allowed` and
`formal_admission_allowed` are both fixed to `false`.

The reference observation establishes only:

- raw opening increases the finite support;
- `open → bind` and `bind → open` differ by the order scar `{3}`;
- the whole-extension difference is `scar_replay`, while deleting history
  collapses that difference;
- the relabel and reversal controls preserve or move the scar as declared; and
- the minimal sufficient MSS candidate is `minimal_exclude_scar`.

The controller computes these facts independently in
`constraintbox.paired_extension`; engine receipts are not treated as the
definition of the fixture.

## Three lanes and envelope

| lane | semantic role | load-bearing operation |
|---|---|---|
| Julia | semantic owner | finite-set derivation plus Z3 positive/erased-history controls |
| JAX | batched mirror | `jax.jit`/`jax.vmap` finite masks plus Z3/CVC5 controls |
| PyTorch | sensitivity mirror | finite masks plus `torch.func.jacrev` retained-vs-erased history control |
| envelope | cross-engine consumer | exact fixture hash and canonical-observation equality, independent Z3/CVC5 controls |

No lane reads a peer result. The envelope reads the three lane receipts only
after they finish, checks their source and result paths, and carries the
divergence table. Tensor exchange is forbidden; the common input is the JSON
fixture and the common output is the controller-defined observation.

## CB registration and rerun

The manifest profile is `paired-extension`. A fresh controller run uses:

```bash
PYTHONPATH=src python -m constraintbox cr-slice \
  --profile paired-extension \
  --cr-root /Users/joshuaeisenhart/Codex-Ratchet \
  --manifest /Users/joshuaeisenhart/Codex-Ratchet/constraint_box/config/cr_sim_slice_v1.json \
  --run-dir /private/tmp/cb-paired-extension-run
```

For the 2026-08-03 isolated run, the receipt was:

`/private/tmp/cb_paired_extension_run_parent.C9QCM9/run/receipt.json`

SHA-256: `60a43f111cbb1c135f7f1c81e04bd5d97027ed8e03260202c895314b31866155`.
It was `4/4 PASS` after the controller rechecked every result, with Julia
1.12.6 and the selected CPython 3.13 runtime. The fixture source hash was
`87ca28eabb83a87abe3a2949bd827f8e7050b348cdd4fbb6971505b931ebe364`.

This is source-addressed external operation evidence. It does not prove CR,
whole-engine readiness, a portable installation, attractor basins, or a
physical/manifold result, and it does not promote the packet into CB admission.
