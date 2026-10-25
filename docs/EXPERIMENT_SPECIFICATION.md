# Frozen Study Configuration (Public Summary)

**Scope:** Describes the frozen configuration that can be corroborated from the original private source manifests. This file is a human-readable publication summary; it is **not** a complete runnable experiment configuration or an assertion that missing inputs are present.

| Property | Recorded setting |
| --- | --- |
| Encoder | `intfloat/multilingual-e5-base` |
| Encoder revision | `d128750597153bb5987e10b1c3493a34e5a4502a` |
| Source Python / compute environment | 3.10.13, macOS MPS |
| Raw embedding dimension | 768 |
| Representation-control ε | 0, 2, 4, 8, 16, 32, 64 |
| Seeds | 7, 13, 42 |
| Retrieval depth | Top 10; score boundary recorded to rank 11 in selected source artifacts |
| Playbook corpora | B1 clean anchor 50; C primary 830; C broad 1606 |
| Primary query set | 30 prepared scenarios (Phase 1 marked 25 primary-valid) |
| BM25 baseline | k1=1.2; b=0.75; Unicode NFKC tokenizer with Hangul bigrams |

Guard control mapping:

| ε | Output dimension | Quantization bits |
|---:|---:|---:|
| 0 | 128 | 4 |
| 2 | 160 | 5 |
| 4 | 192 | 6 |
| 8 | 224 | 7 |
| 16 | 256 | 8 |
| 32 | 320 | 10 |
| 64 | 768 | 16 |

The Guard implementation performs L2 normalization, a seeded Gaussian projection where the dimension is reduced, uniform quantization, and another L2 normalization. Both dimension and quantization precision change across ε. **ε is not a differential-privacy budget or a noise-power estimate.** Raw and Guard at ε=64 are distinct experimental conditions.

## Publication claim boundaries

- B1 relatedness assessments cover **27** queries for the primary graded relevance calculation.
- B1 Raw nDCG@10 ≈ **0.382750**, Guard ε=16 nDCG@10 ≈ **0.431091**. This meets the study-specific 95% Raw-relative *noninferiority* criterion but does not establish *superiority*.
- Operational label coverage on adjacent ε transitions: B1 **457/540**, C primary **336/450**, C broad **342/450**; all fail the study's 95% coverage threshold.
- The operational change figures are available-case analyses; the joint operating region remains **not evaluable** under the frozen coverage criteria.
- Track C graded-relevance retrieval effectiveness was **not evaluable**, not shown to be absent or inferior.

## Provenance and environment caveat

The *private* frozen manifests identify experiment configuration and results. Some underlying clean input files were stored outside the tracked repository, making the published subset incomplete. The public GitHub CI uses Python 3.11 to verify source-level behavior and summary arithmetic; it must **not** be described as a recreation of the source macOS MPS scientific environment.
