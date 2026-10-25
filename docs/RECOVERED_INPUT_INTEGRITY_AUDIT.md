# Frozen Original Input Integrity Audit — 2026-10-25

**Status:** `PASS_EXACT_BYTES_AND_INTERNAL_INPUT_BINDINGS`.  
**Scope:** Four recovered user-supplied JSONL inputs compared against frozen private research input-manifest identifiers. This **does not** mean that all input data have been authorized for public redistribution or that the scientific model/retrieval experiment has been rerun.

| Input file | Records | Bytes | SHA-256 verification |
| --- | ---: | ---: | --- |
| `playbook_source_clean_inputs.jsonl` | 1606 | 7,874,230 | `bafbf21b08f70de1355ea5bb985c4e57421fd35d56deb77b639dc4e168c94d89` — MATCH |
| `query_source_clean_inputs.jsonl` | 30 | 12,226 | `e72be8067f94bf72c69d6cb69e9cbd3e431a8153e1c5ade468283fa9040c453c` — MATCH |
| `anchor_50_clean_binding.jsonl` | 50 | 24,617 | `c404fea3d583a61932c0ca5a0c33212575acd5215468e8490367991c789f237b` — MATCH |
| `token_lengths.jsonl` | 1766 | 781,316 | `9732e3ba440d42397e09a629d648f4c4e573bcc8ef2aac6a0fe63d3b3e31c14a` — MATCH |

## Validation performed on the recovered data

- All four JSONL streams parsed without invalid/empty lines.
- All 1606 playbooks have distinct `electronics_id` values, and all 30 queries have distinct `query_id` values.
- The 1606 playbook encoder-text hashes and their 1606 source-text hashes matched their row contents; both the encoder-text and query-text hashes matched all 30 queries.
- The 50 source playbook bindings matched `electronics_id` and original source SHA-256 in the 1606-playbook input file (50/50).
- All 1766 token-length records were mapped to the corresponding input text's cryptographic hash, with **1766/1766 matches**. Token length/unused-length/truncation arithmetic passed for all 1766.
- Tokenization records comprised C playbooks: 1606; C queries: 30; B0 queries: 30; B0 anchors: 50; B1 anchors: 50.
- Exactly 830 playbook rows were `PRIMARY_MACHINE_SELECTED`; 776 `UNRESOLVED_DEFERRED`.
- Token-length records marked 510/1606 C playbooks truncated to at most 512 tokens; 5/50 each of B0 and B1 anchors were truncated; C and B0 query records were not marked truncated.
- Original anchor split: 28 PRIMARY and 22 UNRESOLVED (matches frozen membership record).

## Publication and reproducibility boundaries

- The complete recovered 1606-playbook input text was **not** copied to this public repository.
- Automated preliminary privacy inspection detected email-like strings within the original playbook text; raw publishing requires targeted review and decisions on third-party content licensing and privacy.
- The original tokenizer token IDs have **not** been regenerated to independently validate tokenizer version or truncation byte-for-byte. Stored token-length and digest bindings were checked, not model execution.
- The complete E5 encoder, Apple MPS numerical stack, source Guard rankings and bootstrap re-execution are **not** reproduced by this audit.
- The 30-query and 1500-relevance-label CSVs and personal reviewer provenance are not published in this repository.

**Current disposition:** Exact original text inputs recovered and cryptographically verified; source-model execution and full reproduction remain separate gates.
