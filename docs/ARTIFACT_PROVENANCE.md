# Artifact provenance and verification scope

## Source identity

The 14 verbatim source artifacts below were copied from an accessible **private research repository** to the public curated repository without modifying the files' contents.

- Private source repository: `bearsgom-commits/guard-soar-reproducibility`.
- Frozen source commit: `7c43a30511cd217cab6bfadf05db77b0c8ab943c`.
- Public repository: `bearsgom-commits/soar-playbook-retrieval-reproducibility`.
- Verification performed at public packaging: the Git blob SHA for each of the 13 files was compared against that same path at the frozen private source commit; **14 of 14 matched**.
- The parent repository and its full commit history remain private. No private source commit history was transferred.

| Curated path | Git blob SHA-1 (content identity) |
| --- | --- |
| `src/guard_repr.py` | `b38fe3a4973926a8fa04924926d92fa245898d69` |
| `src/electronics/__init__.py` | `e0b473a98dcdb01229eb5b650856435dc099d6ec` |
| `src/electronics/bm25_fixed.py` | `cca2f0d3444c73d039ec93f149fea8c9e26d0868` |
| `src/electronics/human_gt_scoring.py` | `a4f8c17b33c7664796a715920f0ca375463c6c78` |
| `tests/test_electronics_bm25_fixed.py` | `204c9ac7b2d0d0713a4170e820e4556e7f7a43ca` |
| `tests/test_electronics_human_gt_scoring.py` | `f943c0c02f0c199619751e8cae177beaea85b3e7` |
| `results/electronics/human_gt/v1/scientific_results/track_b_utility_summary.json` | `a0d67571af05b42c4bf9471e6146c7bed135a860` |
| `results/electronics/human_gt/v1/scientific_results/track_b_noninferiority.json` | `fbd0799a7a2ac81fc427e0a2deda763b08dc254f` |
| `results/electronics/human_gt/v1/scientific_results/track_b_omfr.json` | `4f66f5cbd3d76ede2abd0c569facda0121e42351` |
| `results/electronics/human_gt/v1/scientific_results/track_c_primary_omfr.json` | `e3671f14ecd7fcd598ac31f3c0ac4f631c645d83` |
| `results/electronics/human_gt/v1/scientific_results/track_c_broad_omfr.json` | `2e02597f7d5604e99c59f15d66e8e7405163d6d0` |
| `results/electronics/ranking_propagation/v1/scientific_results/same_epsilon_seed_robustness.csv` | `9e8bdbcb65a3a5f01cc4ef310847d657a50a18b2` |
| `results/electronics/ranking_propagation/v1/scientific_results/ranking_pair_summary.csv` | `c8ad821fe59fea45354d3a5f88ab3c23a31257f4` |
| `results/electronics/human_gt/v1/manuscript_v1/figure_source_data.json` | `d9dd6e2027852114f6d4b5009a244ad8be2bd0be` |

The blob SHA-1 identities confirm **byte-preserving transfers**, not fresh executions or independent replication of the scientific findings.

## What the public verifier checks

Run:

```bash
python scripts/verify_public_aggregates.py
```

It reads the included frozen aggregate JSON and CSV files and checks:

- B1 graded-relevance noninferiority, 27-query denominator, Raw and ε=16 nDCG@10 means;
- B1, C-primary, and C-broad operational label coverage denominators and failure of the 95% coverage gate;
- B1 six adjacent-ε Top-1 flip counts;
- presence of published same-ε seed-robustness rows.

This **does not** recompute the original bootstrap confidence intervals, recreate playbook text, rerun E5 embeddings, rerun the source model's MPS retrieval or re-create human annotations.

## Core experiment identity

- Semantic encoder: `intfloat/multilingual-e5-base`, frozen revision `d128750597153bb5987e10b1c3493a34e5a4502a`.
- Raw representation dimension: 768.
- Seeds: 7, 13, 42.
- Guard settings: ε ∈ {0, 2, 4, 8, 16, 32, 64}.
- Guard dimension / quantization settings: (128,4), (160,5), (192,6), (224,7), (256,8), (320,10), (768,16).
- **ε is a representation-control index, not a formal differential-privacy budget.**
- The ε=64 Guard representation remains different from the Raw baseline.
- Reference hardware for original frozen experiment: macOS MPS, Python 3.10.13. This minimal published subset is not an equivalence guarantee across platforms.

## Study claim boundaries

- Raw B1 nDCG@10: approximately 0.382750. Guard ε=16: approximately 0.431091. The pre-specified Raw-relative 95% noninferiority rule is met at ε=16; **statistical superiority is not thereby established**.
- Operational coverage: B1 457/540 (84.63%); C-primary 336/450 (74.67%); C-broad 342/450 (76.00%).
- The predefined 95% operational-coverage threshold fails in all three tracks; operational change estimates are **available-case exploratory**, not validated population-wide operational stability.
- Expanded Track-C relevance effectiveness and the joint operating region are **not established** under the frozen study contracts.
- Differences across ε include jointly changing projection dimension and quantization; do not interpret observational differences as isolated causal effects.

## Still absent from this public package

The raw multilingual E5 encoded inputs, all Guard source rankings, query/playbook source snapshots, human evaluation row-level provenance, complete analysis runners, external playbook content, and full clean-environment scientific rerun documentation are not yet provided. Some materials may require redaction, data-use permissions, or additional testing. The publication claim must be limited to what is actually present.

**Release status: curated partial public artifact, not full end-to-end reproduction.**
