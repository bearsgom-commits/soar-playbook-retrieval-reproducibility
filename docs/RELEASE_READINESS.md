# Release Readiness and Verified Blockers

**Assessment date:** 2026-10-25.  
**Current disposition:** `PARTIAL_PUBLIC_ARTIFACT_VALIDATED`, **not** `FULL_REPRODUCTION_COMPLETE`, **not** `READY_FOR_FINAL_RELEASE`.

This document lists evidence-based current scope and concrete conditions for an eventual complete release. Absence from the public repository does not imply nonexistence in the underlying research project.

| Gate | Status | Observed evidence / specific obstacle | Required condition to close |
| --- | --- | --- | --- |
| Public repository and initial documentation | **PASS** | Public repository and README available | Keep URLs and claims accurate |
| Verbatim transfer of curated frozen files | **PASS** | 14 of 14 copied file Git blob identities match source commit `7c43a30511cd217cab6bfadf05db77b0c8ab943c` | Recheck once final artifact set is assembled |
| Public unit tests | **PASS, limited scope** | GitHub Actions run of selected tests passed (53 tests); not the historical private 357-test suite | Do not conflate two different runs |
| Aggregate output numeric checks | **PASS, limited scope** | Checks of B1 nDCG@10, retention decisions, track coverage, stability summaries, and plot-source consistency | Add full input-level replay if legitimately available |
| Public aggregate plot regeneration | **PASS** | Two SVG charts generated from stored aggregate figure source data in CI | Label as aggregate visualizations, not fresh scientific figures |
| Research source files sufficient for full replay | **BLOCKED** | Private frozen manifest describes untracked clean text/embedding inputs; source files are not all present in the public or tracked private repository | Researcher must locate authoritative input artifacts and check exact SHA-256, permissions, and exclusions |
| Full query/graded relevance data release | **BLOCKED** | 30-query and 1,500-judgment CSVs were identified and reviewed; upload attempt was blocked by environment safety control. They are not published | Authorized, safe data-publication route with privacy/ethics clearance; do not bypass block |
| Original SOAR playbook text redistribution | **BLOCKED** | Third-party source content and full 830/1606 clean corpus require rights review; raw playbook source is omitted | Document upstream provenance/license and use link-only or approved derivative data as appropriate |
| Individual annotation provenance | **UNVERIFIED** | Frozen per-team/phase records exist privately, but public aggregate files do not verify reviewer identities or participant independence | Honest traceability and any required author/IRB determinations; never fabricate or revise frozen judgments |
| Full scientific experiment regeneration | **NOT EXECUTED IN PUBLIC CI** | No source E5 model encoding, complete Raw/Guard re-ranking, or full 10k bootstrap computation performed in public CI | Compatible environment plus exact inputs/runners; compare frozen output hashes and paper figures |
| Original 357-test report with 44 manifests/16 hashes | **NOT PUBLICLY VERIFIED** | Specific execution logs not published or independently retrieved | Locate dated executable logs and source environment; otherwise do not state 357/44/16 as externally verifiable |
| OS/backend numerical equivalence | **NOT ESTABLISHED** | Private prior experiments noted macOS MPS/CPU numerical differences; public checks run Linux CPU | Test cross-backend within specified tolerances and record divergences |
| Software and data redistribution license | **UNDECIDED** | Public repository has no selected license; some source files may have third-party/organizational obligations | Verify ownership with all rights holders and select approved license, or document restrictions |
| Citable final release tag and DOI | **PENDING** | Snapshot is partial | Create fixed release only when materials and reproducibility claim are vetted |

## What has actually been tested

- GitHub Actions Python 3.11 Linux subset: **53 passed**, including Guard deterministic behavioral checks, BM25 and scoring helper tests.
- Frozen aggregate verifier: reported pass and cross-checked figure numeric values.
- Two generated SVG plots: `track_b_ndcg_public.svg` and `operational_coverage_public.svg`, available as run artifacts.
- The public data package currently **does not contain** private raw text, evaluators' personal information, or full E5/Guard rerun inputs.

## Why final journal claims need restraint

A public GitHub URL alone is **not** evidence that every result in a journal manuscript is fully independently reproducible. A correct journal Data Availability Statement must list which data/code are actually obtainable, restrictions on omitted materials, and any available way to request access. Do not cite a release tag or DOI before it exists.

Do not publish the original private repository history en bloc, and do not remove the block distinctions above merely to mark the release complete.
