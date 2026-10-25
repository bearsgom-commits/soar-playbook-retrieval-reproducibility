# Semantic SOAR Playbook Retrieval: Reproducibility Materials

This repository is being prepared as the **public research-artifact package** for a study of representation-constrained semantic retrieval and downstream SOAR playbook selection in satellite ground-segment-inspired cybersecurity scenarios.

> **Release status — preparation in progress.** This is not yet a complete reproducibility package. Code, eligible datasets, frozen configuration files, results, and execution instructions will be added only after provenance, licensing, privacy, and consistency checks. Do not treat the current repository as proof that the full scientific experiment has been reproduced.

## Study scope

The study examines four distinct aspects of a semantic SOAR playbook retrieval workflow:

- **Retrieval effectiveness:** graded relevance of retrieved playbooks (primarily nDCG@10).
- **Ranking stability:** changes in retrieved ranks and Top-1 selections across representation settings and seeds.
- **Operational attribute propagation:** differences in annotated response-related attributes when the selected playbook changes.
- **Decision boundary:** whether the predefined retrieval and operational assessment criteria can be jointly evaluated and met.

The representation-control parameter **ε is an operational setting, not a differential-privacy budget or a formal privacy guarantee**. Observed changes across ε settings must not be read as an isolated causal effect of any single underlying transformation component.

## Public artifact release plan

| Material | Intended location | Status |
| --- | --- | --- |
| Research implementation and tests | `src/`, `tests/`, `scripts/` | Under review |
| Frozen experimental settings and input provenance | `configs/`, `manifests/` | Under review |
| Legally redistributable scenario and annotation data | `data/` | Under review |
| Aggregated paper results and source-to-table mapping | `results/`, `docs/` | Under review |
| Environment specifications and execution instructions | Root directory and `docs/` | Under review |

See [Public release checklist](docs/PUBLIC_RELEASE_CHECKLIST.md) for the acceptance criteria.

## Reproducibility claim boundaries

Software unit tests, file-integrity checks, recomputation from stored results, and **end-to-end reruns of model encoding and retrieval** are distinct types of verification and will be reported separately. Passing one does not imply that the others have been completed. Any cross-device differences between the source environment and Linux CPU execution will be documented.

## Citation and data availability

The manuscript's final citation information, software release tag, permanent archive DOI (if issued), and exact public-data availability statement will be added **after** the curated artifact package has passed its release checks.

## Source repository

The original development and research-audit repository is maintained separately. Its contents and commit history are **not automatically licensed, anonymized, or approved for public redistribution**.
