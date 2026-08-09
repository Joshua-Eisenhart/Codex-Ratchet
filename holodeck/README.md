# Holodeck v0.1 development scaffold

Holodeck is now a separate product root. It owns trainable prediction,
associative memory, perception, and world-model experiments. It does not own
QIT engines, ConstraintBox, ClaimGate, or Codex Ratchet.

The repository already contains many Holodeck-named probes. V9 indexes them as
candidate sources rather than pretending they already form one engine. The
current product is an independently installable shell and live tool doctor.

PyTorch is an optional Holodeck profile because trainable world-model work needs
it. Julia and QIT engines remain external Sim Engines reached through explicit
bridges. A similar mathematical signature across old probes is not evidence
that the two QIT engines, four loops, or sixteen stages are complete.

```bash
python3 -m venv .venv-holodeck
.venv-holodeck/bin/python -m pip install -e 'holodeck[world-model]'
.venv-holodeck/bin/holodeck doctor --json
.venv-holodeck/bin/python holodeck/scripts/write_status.py
```

The first science gate after this scaffold is a source-independent QIT engine
reality check. Only then should the Holodeck consume QIT observations through
`holodeck-to-qit-engines`.
