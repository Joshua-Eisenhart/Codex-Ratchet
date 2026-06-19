# Builder Self-Assessment - root_randomness_entropy_discriminator_v0

Status: builder packet, not independent audit.

The packet builds a finite discriminator with a real claim ceiling:

- root entropy rows are computed from the pinned finite ensemble before labels or geometry;
- label shuffle preserves root rows but changes label-dependent readouts;
- label-structured control adds measured label quotient information and is not bit-identical to label shuffle;
- geometry-first order changes the finite readout;
- SMT binds computed count/order predicates only, with flip controls.

Residual boundary: a green run means this finite toy has nontrivial root-layer readout separation under declared controls. It does not admit a physics claim or complete any downstream safe-order packet.
