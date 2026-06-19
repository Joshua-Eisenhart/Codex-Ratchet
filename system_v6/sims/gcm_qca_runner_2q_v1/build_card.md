# gcm_qca_runner_2q_v1 Build Card

Coordinates: `dynamics | integrated-onto-the-carve | 2Q`.

Classification and ceiling: `scratch_diagnostic`, `carrier-and-pins-relative`; no promotion and no formal admission.

Purpose: repair `gcm_qca_runner_2q_v0` after the fresh-verification catch at `10bf57a1f`: the v0 L-to-R swap control re-called the R constructor and therefore proved a construction tautology. This v1 takes the realized L unitary, applies spatial reflection as an independent matrix operation, and compares that reflected L to the independently built R.

Substrate: consume `gcm_2q_object_id` `gcm2qobj_715e9424ea66468243108751fb59395f` and registry body hash `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`. The registry audit is in flight, so every 2Q carve-preservation claim is conditional on the 2Q registry audit verdict.

QCA/GNVW boundary: the computed nonzero row is the finite open-chain support-rank formula on realized 2Q-site unitaries. The finite periodic ring is used only as a local brickwork/light-cone witness; no nonzero finite-ring automorphism-class GNVW index is claimed.

Mirror repair controls: reflection is an involution; the reflected-L row is built by `P_out * U_L * P_in^dagger` with no constructor re-call; a non-mirror permutation must stay red; the old constructor swap is retained only as `BY_CONSTRUCTION` regression evidence. The bare reflected L need not equal R for the packet to validate; the equality/non-equality is the measured result.

Controls: quantization check, nonchiral index-0 rule, balanced swap index-0 rule, independent reflected-L sign flip, output-local gauge preservation, dressed-conjugacy scan, non-mirror permutation negative, and carve-erasure substrate negative.

Fence: this is the first runtime-flux/chirality piece. The full runtime flux family, including `J_ent`, `J_cut`, and related current rows, stays gated on 3Q.

G.2a boundary: builder output sets `no_builder_audit_verdict=true` and uses `scripts/builder_audit_boundary.py`; this builder card is not an audit verdict.
