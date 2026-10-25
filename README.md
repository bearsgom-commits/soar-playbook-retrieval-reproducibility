# Semantic SOAR Playbook Retrieval — Research Artifacts

Public **curated research artifact subset** for an investigation of representation-constrained semantic retrieval and SOAR playbook selection changes in satellite ground-segment-inspired cybersecurity scenarios.

> **Status: partial reproducibility package (not final release).**
> Frozen aggregate outputs and selected research implementation/tests are available. Source playbook snapshots, full ranking inputs, all human-judgment rows, and a validated end-to-end reproduction workflow are **not** available here yet. The existence of this repository must not be interpreted as end-to-end reproduction of the scientific experiment.

## What is available now

| Paths | What you can inspect |
| --- | --- |
| `src/guard_repr.py` | Original Guard projection and quantization source |
| `src/electronics/bm25_fixed.py` | Fixed lexical BM25 baseline module |
| `src/electronics/human_gt_scoring.py` | Frozen human-ground-truth metric definitions and helpers |
| `tests/` | Selected BM25 and metric unit tests |
| `results/electronics/human_gt/v1/scientific_results/` | Frozen **aggregate** B1 retrieval and operational-attribute result JSON files |
| `results/electronics/ranking_propagation/v1/scientific_results/` | Frozen aggregate ranking and same-ε robustness CSV files |
| `results/electronics/human_gt/v1/manuscript_v1/figure_source_data.json` | Frozen aggregate plot source values | 
| `scripts/verify_public_aggregates.py` | Bounded consistency checks of published aggregate output |
| `docs/ARTIFACT_PROVENANCE.md` | Frozen private source commit, all 13 copied-file blob hashes, limitations |

Exactly **14 included source files were verified to match their frozen originals** by Git blob hash. This establishes the file transfers' identity, not independent experiment reproduction. Other files in this repository are newly authored release documentation or checks.

## Run the currently available checks

Python 3.11 or later is suggested for this small public subset, but this does **not** reconstruct the original macOS MPS scientific environment.

```bash
python -m pip install -r requirements-public.txt
python scripts/verify_public_aggregates.py
PYTHONPATH=src python -m pytest -q \
  tests/test_electronics_bm25_fixed.py \
  tests/test_electronics_human_gt_scoring.py \
  tests/test_public_guard_repr.py
```

See [detailed instructions](docs/RUN_PUBLIC_CHECKS.md), [artifact provenance](docs/ARTIFACT_PROVENANCE.md), and [pre-release checklist](docs/PUBLIC_RELEASE_CHECKLIST.md).

## Core interpretation limits

- Retrieval effectiveness is measured by graded relevance metrics such as nDCG@10; search-speed or analyst task outcomes are **not** inferred.
- Guard ε is a joint **representation-control setting**, not a differential-privacy budget. Projection dimension and quantization bits change together across ε.
- B1 Raw nDCG@10 ≈ 0.38275 and Guard ε=16 nDCG@10 ≈ 0.43109. The 95% noninferiority criterion is met at ε=16, without establishing superiority.
- Operational coverage fails the study's 95% gate (B1 84.63%, C-primary 74.67%, C-broad 76%). Available-case estimates are exploratory, **not validated joint-operating regions**.
- Software unit tests and frozen-output checks are **not** a complete encoder/retrieval rerun.

## Dataset and software rights

No third-party SOAR playbook source material, individual reviewer identity records, or unreviewed private audit logs are included in this initial release. Provenance, privacy, redistribution rights, and requirements for full scientific replay must be checked before any further publication. No open-source reuse license has yet been adopted; contact the authors before reuse beyond rights provided by law.

## Latest verified CI status

- Selected unit tests: **53 passed** on GitHub Actions (Python 3.11 / Linux CPU).
- Frozen aggregate consistency verification: **PASS**.
- Two aggregate plots generated from source JSON in CI: **PASS**.
- [Verification run](https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility/actions/runs/40196919959)
- [Current release-readiness blockers](docs/RELEASE_READINESS.md)
- [Source-verified experiment settings](docs/EXPERIMENT_SPECIFICATION.md)
- [Results-to-file mapping](docs/RESULT_TO_ARTIFACT_MAPPING.md)

## Manuscript citation

A permanent release tag, scholarly citation and optional archival DOI will be added once the release package, code/data rights, and validation status are finalized. Cite the final tagged release, **not** this incomplete preliminary snapshot, for submission.
