# Data and Code Availability — Working Draft

**This is a draft for manuscript preparation, not a final submission declaration.**

> Selected research implementation, unit tests, aggregate retrieval-effectiveness results, aggregate ranking-stability results, and aggregate operational-attribute evaluation summaries are available in the public GitHub repository at https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility . The current repository is a curated partial research artifact. Raw playbook text, complete experiment input snapshots, individual reviewer records and complete end-to-end model execution materials are not included. The available aggregate checks and unit tests do not constitute a full independent rerun of the original scientific experiment. Dataset access restrictions and the scope of further public release remain under review.

## Pre-submission checklist

- [ ] Include the **actual tagged release URL** or archived DOI once the public package is finalized.
- [ ] Explain any permanent access restrictions for source playbooks and original judgment records; do not imply that unpublished source data are openly available.
- [ ] Confirm that the source-data redistribution permission and observer privacy review are complete.
- [ ] Reconcile evaluation-source claims in the manuscript against original frozen reviewer data.
- [ ] Confirm final author contributions and corresponding-author approval.
- [ ] Retain accurate claim boundaries: the 95% operational-label coverage requirement was not met.
- [ ] If the release stays partial, describe it explicitly as partial support rather than complete reproducibility.

## Current verified package status

- 14 pinned original code/result/figure-source files are published, matching the source blob SHA values.
- A public validation script cross-checks aggregate values and figure data.
- Public GitHub Actions on Python 3.11 succeeded: **37 selected unit tests passed**.
- **Not** the privately reported 357-test suite; not an end-to-end E5/Guard rerun.
- Query-level and relevance-qrel row-level CSV files are **not** available in this public repository. Their release is subject to additional privacy/distribution review.

Do not describe this repository as containing a complete replication dataset until the omitted artifacts have actually been released and tested.
