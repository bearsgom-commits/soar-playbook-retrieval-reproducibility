# Data and Code Availability — Draft updated 2026-10-26

**Working draft, not a verified final publisher statement.**

The public research repository at https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility contains selected research code and tests, the 30-query domain-validity dataset, 1,500 graded relevance judgments, the author-approved original input ZIP including 1,606 playbook clean-input records, source membership manifests (830 and 1,606), frozen Guard ranking records for four tracks, and aggregate results. Relevant upstream MIT source-attribution text is included.

Public result-derived checks reproduce seven B1 Guard nDCG@10 means from released graded relevance judgments and saved ranks; 24 adjacent-setting ranking summaries and 28 same-setting seed summaries also match the frozen outputs. In a **separate** GitHub Actions full E5/Guard re-encoding and retrieval run on a macOS MPS runner, the original input SHA-256 checks passed and model execution completed, but frozen Top-10 rankings were **not** reproduced (0 out of 2,520 exact matches, see [documented mismatch](FULL_RERUN_MISMATCH_AUDIT_20261026.md)). Thus, **complete independent scientific reproducibility is not established**.

The historical original Raw ranking files and selected private original audit logs are not yet supplied in this repository. Original human evaluation identity/provenance details are deliberately not made public in this subset. The published materials must not be described as a successful full reproduction until the discrepancies are resolved, or the limitations are explicitly acknowledged in the final paper.

## Release checklist

- [x] Public repository with source-identical query/qrels and corpus membership manifests
- [x] Original four input-file hashes and publicly hosted original input ZIP
- [x] Frozen ranking and aggregate numeric checks
- [x] Source-compatible-model family MPS replay executed with preserved output
- [ ] **Resolve or fully disclose original-versus-fresh ranking disagreement**
- [ ] Locate and audit original Raw ranking and embedding provenance
- [ ] Locate original historical 357-test execution logs
- [ ] Confirm final author approval, exact license obligations and publisher reporting wording
- [ ] Issue immutable GitHub release and optionally archival DOI; only claim validated scope
