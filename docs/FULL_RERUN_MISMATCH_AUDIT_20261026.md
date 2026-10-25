# Full E5/Guard rerun: observed mismatch and diagnostic disposition

**Audit date:** 2026-10-26 (Asia/Seoul).  
**Primary scientific rerun:** [GitHub Actions run 40235275466](https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility/actions/runs/40235275466).  
**Independent saved-result mismatch diagnostics:** [GitHub Actions run 40236322833](https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility/actions/runs/40236322833).

**Status: SCIENTIFIC_REPLAY_EXECUTED_BUT_RANKING_EQUIVALENCE_FAILED.** The model and original data were successfully processed, but exact reproduction of previously frozen ranked outcomes was **not** achieved. A successfully completed workflow *step* must not be conflated with scientific agreement.

## Checks that passed

- The four original source-input JSONL SHA-256 hashes, counts, and anchor binding checks passed.
- The fixed E5 model snapshot was loaded on Apple MPS using the recorded revision; its 512-token encoder contract was checked.
- All original input arrays were newly encoded and Guard transformed for four tracks and seven ε levels with three seeds. Reference results were not overwritten.
- Comparison outputs were preserved as GitHub Actions artifact `scientific-replay-comparison-mps` in the above scientific run.
- A separate read-only diagnostic downloaded that artifact and compared saved output against published frozen Guard ranking records.

## Measured failures — exact Top-10 and Top-1 matches

| Track | Exact Top-10 matching, among 630 | Top-1 matching, among 630 |
| --- | ---: | ---: |
| B0 anchor | **0** | 116 |
| B1 anchor | **0** | 86 |
| C primary (830) | **0** | 17 |
| C broad (1606) | **0** | 10 |
| **Total** | **0 / 2520** | **229 / 2520** |

The result rules out claiming complete retrieval replay. Top-10 sets also differ substantially; this is not *only* a matter of different ordering within the same ten candidates.

## Epsilon-specific mean Top-10 set overlap

Overlap is intersection-size / 10, averaged over 3 seeds × 30 queries.

| Track | ε=0 | ε=8 | ε=16 | ε=32 | ε=64 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 | 0.2856 | 0.4711 | 0.4167 | 0.4911 | 0.4300 |
| B1 | 0.2722 | 0.4178 | 0.5011 | 0.4611 | 0.4367 |
| C primary | 0.0267 | 0.1067 | 0.0933 | 0.1367 | 0.2033 |
| C broad | 0.0256 | 0.0733 | 0.0878 | 0.1011 | 0.1533 |

For C broad ε=64, a 0.1533 mean overlap means approximately 1.53 shared playbooks among 10, on average. The larger corpora exhibit more severe divergence.

## Still valid — distinct kind of reproducibility evidence

- Frozen source rankings yield the same 24 adjacent-ε and 28 same-ε seed summaries as the published frozen aggregate results.
- The public 1,500 graded relevance judgments reproduce the seven published B1 Guard mean nDCG@10 values from *frozen* ranking records.
- These checks establish **saved-result internal consistency**. They do not verify a new model execution yielding those saved results.

## Scientific diagnosis — not yet established

Possible causes must be tested individually; none is confirmed:

1. Original embeddings reused by the historical Guard ranking run might differ from embeddings freshly produced by the published encoder runner despite matching model revision and input file hashes; compare frozen embedding hashes and numerical vectors, if available.
2. Original encoder tokenization, treatment of prompt prefixes, truncation and model/library details may differ. Inspect recorded E5 code and source execution logs without silently changing the protocol.
3. Distinguish Raw semantic ranking mismatch from Guard representation mismatch. The four frozen Raw ranking records must be recovered and compared before attributing causality to Guard.
4. Differences in backend, batch size, Python patch versions or numerical operators may affect close scores, but must **not** be asserted as the cause of these substantial candidate-set differences without independent evidence.
5. Audit stored playbook identifier ordering, exact per-track corpus views, and score/ranking tie-break contract.

The scientific protocol and frozen output must remain immutable. Every diagnostic, code fix or independent rerun requires an isolated output location and explicit distinction between original frozen analysis and later reproduction.

## Required exact frozen Raw ranking files

The historical `guard_experiment_manifest.json` identifies:

| Missing frozen Raw ranking artifact | SHA-256 |
| --- | --- |
| `B0_anchor_RAW_rankings.jsonl` | `d2bfbc3998c15a4226f127bdb3903f76e4c3df01a1f6ef5f360cd13d74592de7` |
| `B1_anchor_RAW_rankings.jsonl` | `28cc687e5fbf3295579200f816e7e00d8a72442b871c6d50f0e357a83ad0e6db` |
| `C_primary_RAW_rankings.jsonl` | `2f9265553d28f2380749b3b736aa869c142294782e350099d8610511d685102d` |
| `C_broad_RAW_rankings.jsonl` | `3eca0407be9cf7acacec636488bd346d8bffb66f72369cf91fbf8bf627601383` |

These files are not currently present in the public release. Recovery from dated local audit records and SHA-256 verification precede any public comparison or claim.

## Release gate

**STOP** any final tag, Zenodo DOI, or manuscript claim of complete end-to-end reproduction until this discrepancy has been resolved or formally disclosed with accurate limited-scoped Data Availability and Reproducibility statements.
