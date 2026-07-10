# Packet 102 Canonical Rerun Audit

Status: mechanically green, scientific additions not admitted.

## Package Lock

- source: `/Users/joshuaeisenhart/Desktop/102.zip`
- package SHA-256:
  `d7059778fcc4f1a85b537d8b70e57e4a68f17f538ef415d4943b88696ba85136`
- ZIP integrity: pass
- members: 465
- live comparison at intake: 442 byte-identical, 19 different, 4 absent
- packaged `run_all_report.json`: absent

The four package-only members are the UP-133 co-ratchet depth source/result and
the UP-134 MOND source/result. They were not copied into the live sim tree.

## Reruns

The first isolated rerun used bare Python and returned `133 pass / 2 fail / 4
skip`. Both failures were `ModuleNotFoundError: pysindy`; the four skips were
optional QIT/JAX paths. This is preserved as a wrong-runtime receipt and is not
the package verdict.

The exact same extracted package was then run with:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 run_all.py
```

That canonical rerun returned `139 pass / 0 fail / 0 skip`. The report hash is
`daf03db6cad5649233789b619ad8fd329bde101ffe277123822f6dbc15c852e5`.

This proves the package harness is executable in the intended environment. It
does not prove every script's interpretation because `run_all.py` gates process
exit codes and self-declared checks, not independent claim validity.

## Scientific Disposition

### UP-130

The packaged source is byte-identical to the already-audited UP-130 source
(`sha256:6d412087c47b12dbf82b982589c801e531e8fff1c0398bdb117a64bd084b3741`).
The live fabrication audit rejects its derivation: the count predicate fixes
four, the claimed quarter-turns are 180-degree Bloch rotations, the adjoint
channels commute, all legs preserve entropy, the controls do not isolate, and
`ABAB`/`BABA` are one cyclic orbit. Its package green remains rejected.

### UP-133

UP-133 removes UP-130's explicit two-A/two-B prefilter, so its bounded
minimality scan is a real improvement. It still does not establish the claimed
co-ratchet architecture:

- cyclic alternation over a two-letter alphabet already restricts candidates
  to even lengths;
- its two legs are the same 180-degree Pauli adjoint involutions whose channels
  commute;
- both legs are unitary, so the purported entropy axis has no entropy movement;
- the resulting length-four closure is a property of this selected pair of
  involutions, not a derivation of Ti/Te/Fi/Fe or the source 16-by-4 engine;
- its R5 floor only shows that splitting one fixed-axis rotation into
  same-generator substeps preserves the net map, a one-parameter group
  identity rather than a proof that all finer structure is free.

Allowed claim: a finite binary alternating-word scout has minimum closing
length four for its chosen Pauli adjoint maps. Blocked: earned co-ratchet depth,
four source substages, engine mechanics, Axis0, perception, objects, or physics.

### UP-134

UP-134 inserts the established numerical relation `a0 = c H0 / (2 pi)`, four
hand-entered galaxy mass/velocity anchors, and the deep-MOND BTFR equation. Its
checks show those chosen values are numerically compatible. No executable
bridge derives `a0` from the Ratchet's Axis0, entropy gradient, or cosmogenesis
objects. A Planck-scale mismatch and a factor-10,000 acceleration perturbation
are weak scale controls, not derivation controls.

Allowed claim: the known MOND/Hubble-scale coincidence and selected BTFR anchors
are numerically reproduced. Blocked: first Ratchet physics prediction,
zero-parameter derivation, GR/LambdaCDM replacement, or physics admission.

## Claim Ceiling

`packet_rerun_and_fabrication_audit_only`. The packet is mechanically green,
while UP-130 remains rejected and UP-133/UP-134 remain unadmitted external
scratch proposals. Axis0, canonical engines, four-substage emergence,
perception, objects, MMMs, ontologies, mesh authority, and physics remain red.
