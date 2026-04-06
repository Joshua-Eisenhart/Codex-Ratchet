**CANDIDATE_PROPOSAL_v1**  
  
**[ASSUME] CP01 FROZEN_STACK_AUTHORITY: All named frozen admissibility specifications are authoritative and are not modified by any candidate proposal document.**  
  
**[DERIVE] CP02 CANDIDATE_DOCUMENT_FORM: A candidate proposal is a finite plain-text document consisting only of (i) a candidate header token, (ii) declarations, (iii) witness declarations, (iv) compatibility claims, (v) failure conditions, and (vi) optional OPEN-only candidate-family listings.**  
  
**[DERIVE] CP03 CANDIDATE_HEADER_TOKEN: The first non-empty line of a candidate proposal document MUST be a single fixed token string naming the candidate; this token string is the candidate’s identity and must be treated as uninterpreted.**  
  
**[DERIVE] CP04 NO_RENAMING_RULE: A candidate proposal MUST NOT rename, paraphrase, alias, or reinterpret its own header token, and MUST NOT rename, paraphrase, alias, or reinterpret any frozen specification name or frozen symbol name it references.**  
  
**[DERIVE] CP05 VERSIONING_AS_TOKEN_ONLY: Any versioning of a candidate identity MUST be encoded only in the candidate header token string; no semantic meaning of version increments is admitted at the kernel level.**  
  
**[DERIVE] CP06 DECLARATION_BLOCK_REQUIRED: A candidate proposal MUST contain a declaration block that enumerates exactly the set of new symbols it proposes and exactly the set of frozen symbols it uses.**  
  
**[DERIVE] CP07 NEW_SYMBOL_DISCIPLINE: New symbol declarations MUST be limited to (i) finite token registries, (ii) relation symbols over previously admitted token types, and (iii) classifier symbols over previously admitted token types; no other new primitive kinds are permitted by default.**  
  
**[DERIVE] CP08 FROZEN_SYMBOL_USAGE_LIST: A candidate proposal MUST list all frozen symbols it invokes; omission of an invoked frozen symbol from the usage list is a failure condition.**  
  
**[DERIVE] CP09 WITNESS_BLOCK_REQUIRED: A candidate proposal MUST contain a witness block whenever it makes any claim about non-commutation, obstruction, nontriviality, order-sensitivity, non-flattenability, incompatibility, or any other claim that would otherwise be ungrounded.**  
  
**[DERIVE] CP10 WITNESS_SYNTAX_ONLY: A witness is admissible only as a finite syntactic binding between declared symbols/tokens; witnesses MUST NOT be treated as semantic, evidentiary, evaluative, probabilistic, temporal, or causal objects.**  
  
**[DERIVE] CP11 WITNESS_TYPING: Each witness declaration MUST specify the witness token name and the finite tuple of declared tokens/symbols it binds; witness typing MUST be explicit and must not assume identity or equality.**  
  
**[DERIVE] CP12 COMPATIBILITY_CLAIM_BLOCK_REQUIRED: A candidate proposal MUST contain a compatibility claim block that lists which frozen specifications it claims to satisfy.**  
  
**[DERIVE] CP13 CLAIM_FORM: Each compatibility claim MUST be stated as a finite declarative statement referencing only declared symbols and/or listed witnesses; each claim MUST be written so that its well-formedness can be checked by finite inspection of the candidate’s declaration and witness blocks.**  
  
**[DERIVE] CP14 NO_IMPLIED_ADMISSIBILITY: A candidate proposal MUST NOT assert that any structure is admissible “by default,” “implicitly,” or “because it is standard”; admissibility must be claimed only via explicit compatibility claims against the frozen stack.**  
  
**[DERIVE] CP15 FAILURE_CONDITION_BLOCK_REQUIRED: A candidate proposal MUST contain an explicit failure condition block enumerating falsifiers as syntactic conditions (e.g., undefined symbol use, forbidden symbol introduction, missing witness where required, prohibited implication claims).**  
  
**[DERIVE] CP16 NO_PATCHING_RULE: A candidate proposal MUST declare that if any listed failure condition holds, the candidate is eliminated as a candidate; no patching, repair, reinterpretation, or partial acceptance is permitted within the candidate document format.**  
  
**[DERIVE] CP17 NON_BACKFLOW_GUARANTEE: Candidate elimination MUST NOT modify, weaken, override, or retroactively reinterpret any frozen admissibility layer; candidate failure affects only the candidate’s status, not the frozen stack.**  
  
**[DERIVE] CP18 FORBIDDEN_PRIMITIVE_IMPORTS: A candidate proposal MUST NOT introduce as admitted primitives any time-like, probability-like, causality-like, optimization-like, ontological, or teleological structure; if referenced, such items must be confined to OPEN-only listings and must not be used to justify compatibility claims.**  
  
**[OPEN] CP19 CANDIDATE_FAMILY_LISTING: A candidate proposal MAY include an OPEN-only list of candidate-family header tokens as non-binding placeholders; listing a family does not assert existence, preference, correctness, or admissibility.**  
  
**[OPEN] CP20 FUTURE_FORMAT_REFINEMENTS: Additional format constraints (e.g., canonical ordering of blocks, stricter typing grammars, stronger witness schemas) are OPEN provided they do not introduce new admitted primitives and do not alter any frozen admissibility layer.**  
