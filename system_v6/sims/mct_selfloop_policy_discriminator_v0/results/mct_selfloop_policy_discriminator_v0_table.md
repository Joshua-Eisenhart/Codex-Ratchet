# mct_selfloop_policy_discriminator_v0 table

Decision status: owner-gated. This table makes no recommendation.

| consequence | erase | retain | differs |
|---|---:|---:|---|
| unique folded relation edge count | 1 | 3 | true |
| transported source edge rows retained | 2 | 198 | true |
| transported source edge rows erased/lost from relation | 196 | 0 | true |
| unique self-loop relation edge count | 0 | 2 | true |
| terminal folded node count | 1 | 1 | false |
| may/existential basin folded node count | 2 | 2 | false |
| must/universal omega basin folded node count | 2 | 1 | true |
| H_edge_type_after_policy_nats | 0.0 | 0.056465174279 | true |

## Downstream Consumer Impact

| packet | erase consequence | retain consequence |
|---|---|---|
| `mct_dynamic_admissibility_packet_v0` | policy value would read erase/owner-selected erase; folded relation edge count uses the erase branch; retained self-loop transport rows require explicit loss ledger | policy value would read retain/owner-selected retain; folded relation edge count uses the retain branch; self-loop transport rows remain relation rows |
| `mct_nonassoc_weld_packet_v0` | any inherited folded-relation row must show erased self-loop records and a killed-information/record-loss ledger | any inherited folded-relation row may keep quotient self-loop rows as relation records |
| `basin_rc_transition_graph_v0 consumers of folded G0 quotient` | terminal closed classes stay the same, but folded nonterminal class has no self-loop and becomes forced-exit under must semantics | terminal closed classes stay the same, but folded nonterminal class has a self-loop and is not forced-exit under must semantics |
| `evening_mining_estate_s11_20260611 owner-decision row` | row can be closed only by owner choice; discriminator supplies erase consequences but not preference | row can be closed only by owner choice; discriminator supplies retain consequences but not preference |
