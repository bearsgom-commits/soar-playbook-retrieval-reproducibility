# Release Readiness and Verified Blockers

**Assessment date:** 2026-10-26 (updated after full MPS rerun).  
**Current disposition:** `PARTIAL_PUBLIC_ARTIFACT_VALIDATED`, **not** `FULL_REPRODUCTION_COMPLETE`, **not** `READY_FOR_FINAL_RELEASE`.

This document lists evidence-based current scope and concrete conditions for an eventual complete release. Absence from the public repository does not imply nonexistence in the underlying research project.

| Gate | Status | Observed evidence / specific obstacle | Required condition to close |
| --- | --- | --- | --- |
| Public repository and initial documentation | **PASS** | Public repository and README available | Keep URLs and claims accurate |
| Verbatim transfer of curated frozen files | **PASS** | 14 of 14 copied file Git blob identities match source commit `7c43a30511cd217cab6bfadf05db77b0c8ab943c` | Recheck once final artifact set is assembled |
| Public unit tests | **PASS, limited scope** | GitHub Actions run of selected tests passed (53 tests); not the historical private 357-test suite | Do not conflate two different runs |
| Aggregate output numeric checks | **PASS, limited scope** | Checks of B1 nDCG@10, retention decisions, track coverage, stability summaries, and plot-source consistency | Add full input-level replay if legitimately available |
| Public aggregate plot regeneration | **PASS** | Two SVG charts generated from stored aggregate figure source data in CI | Label as aggregate visualizations, not fresh scientific figures |
| Frozen 4 input JSONL files recovered and verified | **PASS: PUBLIC INPUT ZIP, checks passed** | Four original JSONLs are now contained in the author-approved published ZIP, SHA-256 matched, 1,766 token-to-input digests matched | Preserve immutable ZIP and check reported provenance; see [input integrity audit](RECOVERED_INPUT_INTEGRITY_AUDIT.md) |
| Full query/graded relevance data release | **BLOCKED** | 30-query and 1,500-judgment CSVs were identified and reviewed; upload attempt was blocked by environment safety control. They are not published | Authorized, safe data-publication route with privacy/ethics clearance; do not bypass block |
| Original SOAR playbook text redistribution | **PUBLISHED AS AUTHOR-APPROVED ZIP** | Full derived corpus is available under `input_packages/`; upstream MIT license notice preserved | Maintain rights, attribution and content review. Publication does not prove scientific replay |
| Individual annotation provenance | **UNVERIFIED** | Frozen per-team/phase records exist privately, but public aggregate files do not verify reviewer identities or participant independence | Honest traceability and any required author/IRB determinations; never fabricate or revise frozen judgments |
| Full scientific experiment regeneration | **EXECUTED — RANKING MATCH FAILED** | Run 40235275466 performed full E5 + Guard on verified inputs, but exact Top-10 agreement was **0/2520**. Top-1 agreement 229/2520. No original frozen result was changed. | Analyze Raw and embedding-stage drift, then rerun separately; see [mismatch audit](FULL_RERUN_MISMATCH_AUDIT_20261026.md) |
| Original 357-test report with 44 manifests/16 hashes | **NOT PUBLICLY VERIFIED** | Specific execution logs not published or independently retrieved | Locate dated executable logs and source environment; otherwise do not state 357/44/16 as externally verifiable |
| OS/backend numerical equivalence | **NOT ESTABLISHED** | Private prior experiments noted macOS MPS/CPU numerical differences; public checks run Linux CPU | Test cross-backend within specified tolerances and record divergences |
| Software and data redistribution license | **UNDECIDED** | Public repository has no selected license; some source files may have third-party/organizational obligations | Verify ownership with all rights holders and select approved license, or document restrictions |
| Citable final release tag and DOI | **PENDING** | Snapshot is partial | Create fixed release only when materials and reproducibility claim are vetted |

## What has actually been tested

- GitHub Actions Python 3.11 Linux subset: **53 passed**, including Guard deterministic behavioral checks, BM25 and scoring helper tests.
- Frozen aggregate verifier: reported pass and cross-checked figure numeric values.
- Two generated SVG plots: `track_b_ndcg_public.svg` and `operational_coverage_public.svg`, available as run artifacts.
- Four original JSONL inputs have been published in a verified ZIP. The full E5/Guard replay was executed but did not reproduce the frozen rankings. Individual reviewer provenance remains excluded; historical P9 original audit logs are not yet independently verified.

## Why final journal claims need restraint

A public GitHub URL alone is **not** evidence that every result in a journal manuscript is fully independently reproducible. A correct journal Data Availability Statement must list which data/code are actually obtainable, restrictions on omitted materials, and any available way to request access. Do not cite a release tag or DOI before it exists.

Do not publish the original private repository history en bloc, and do not remove the block distinctions above merely to mark the release complete.
