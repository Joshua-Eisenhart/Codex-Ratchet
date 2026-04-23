  
STATE_ABSTRACTION_ADMISSIBILITY_v1  
  
The name is a fixed token.  
Do NOT rename it.  
Do NOT paraphrase it.  
Do NOT explain it.  
  
SCOPE  
This specification defines when and how a “state” may be admitted as an abstraction  
over cosmologically admissible structures.  
It does NOT define geometry, manifolds, metrics, axes, interpretation, or purpose.  
  
DEPENDENCIES (ASSUME)  
COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1 is frozen and authoritative.  
  
STRICT RULES (HARD)  
- Do NOT introduce ontology (what exists or must exist).  
- Do NOT introduce teleology (purpose, goal, outcome).  
- Do NOT introduce geometry, manifolds, metrics, coordinates, charts, or axes.  
- Do NOT introduce time, probability, randomness, causality, or optimization.  
- Do NOT introduce interpretation layers or narrative framing.  
  
OUTPUT REQUIREMENTS  
- Output MUST be plain text.  
- Output MUST begin with the exact header:  
  "STATE_ABSTRACTION_ADMISSIBILITY_v1"  
- Output MUST contain only:  
  - formal definitions,  
  - admissibility conditions,  
  - non-admissibility statements.  
- Every nontrivial statement MUST be tagged with exactly one of:  
  ASSUME / DERIVE / OPEN  
  
REQUIRED CONTENT (IN ORDER)  
  
1) State Token Admissibility (DERIVE)  
   - When a state token may be introduced  
   - What it abstracts over (finite relation-instances only)  
   - Explicit non-assumptions  
  
2) Distinguishability Without Equality (DERIVE)  
   - How states may be distinguished without primitive equality  
   - Use of relational witnesses only  
  
3) Non-Collapse Conditions (DERIVE)  
   - What prevents state collapse into identity or equivalence by default  
  
4) Admissible State Relations (DERIVE / OPEN)  
   - What relations between states are allowed  
   - What relations are forbidden  
  
5) Open Extensions (OPEN ONLY)  
   - Possible future notions (equivalence classes, quotients, embeddings)  
   - No assertion that these must or will exist  
  
FAIL CONDITIONS  
The output is INVALID if it:  
- introduces geometry, manifolds, metrics, or axes  
- introduces ontology or teleology  
- treats “state” as primitive identity  
- introduces untagged claims  
  
SUCCESS CONDITION  
The output is valid if:  
- “state” is purely an admissible abstraction,  
- no identity or equality is assumed,  
- removing this specification does not alter earlier constraints.  
