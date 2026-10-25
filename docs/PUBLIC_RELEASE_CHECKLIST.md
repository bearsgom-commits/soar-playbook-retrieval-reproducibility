# Public Release Checklist

**Status:** RELEASE NOT YET APPROVED  
**Purpose:** Curate a scientific reproducibility package without exposing unrelated private research materials.

## 1. Publication scope and scientific validity
- [ ] Verify the final paper title, author list, and approved manuscript version.
- [ ] Establish the exact scientific source commit and frozen result manifests used by each paper table and figure.
- [ ] Separate prior conference experiment artifacts from the current study's extended retrieval/annotation analysis.
- [ ] Ensure no unverified end-to-end reproduction claims; report tests, hashes, result recomputation, and fresh model reruns separately.
- [ ] Document limitations of noninferiority analysis, available-case operational results, and unevaluable endpoints.
- [ ] Do not alter frozen scientific labels, observations, or metric definitions during packaging.

## 2. Safety, rights, and privacy
- [ ] Scan files and full intended public commit history for secrets, access tokens, private paths, and user-identifying information.
- [ ] Confirm licenses and attribution requirements for any externally sourced SOAR playbooks or derived materials.
- [ ] Avoid publishing operationally sensitive or proprietary playbook content unless redistribution is authorized.
- [ ] Do not publish annotator names, contact details, or reviewer assignment mappings absent a clear publication need and consent.
- [ ] Include only legitimately public or otherwise redistributable datasets, with provenance.
- [ ] Check that the public package does not inadvertently reveal irrelevant private logs or unpublished research.

## 3. Package completeness
- [ ] Curated implementation, dependency pins, and environment specifications.
- [ ] Frozen search configurations, seeds, model revision, and complete ε-to-representation mapping.
- [ ] Source data access instructions and integrity hashes where lawful.
- [ ] Relevance labels and operational attribute data that may legally and ethically be distributed.
- [ ] Executable test and analysis commands with expected outputs.
- [ ] Machine-readable tables/figure-source manifest or audit mapping.
- [ ] Document known macOS MPS vs Linux CPU numerical and ranking differences.

## 4. Verification and release
- [ ] Recompute the published aggregate tables from included artifacts.
- [ ] Check all public file SHA-256 values and confirm no missing dependencies.
- [ ] Validate public instructions in a clean environment where practicable.
- [ ] Verify README links, license choice, attribution, and data availability text against released contents.
- [ ] Create an immutable release tag (e.g., v1.0.0) only after review.
- [ ] Optionally archive the tagged release for a persistent DOI.
- [ ] Copy the exact validated URL/tag/DOI into the final manuscript, not a hypothetical future URL.

## Release decision

Release only after the checklist items relevant to the claimed level of reproducibility have been verified. Any omitted component must have an explicit limitation statement.

**Current public repository:** https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility
