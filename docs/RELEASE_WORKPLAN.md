# Publication Release Gates — Executable Sequence

**Status: working plan, not a promise of asynchronous execution.** Verify every gate before claiming its outcome. Work on corpus rights review and audit-log recovery may proceed in parallel.

| Gate | Prerequisite / observed current state | Acceptance criterion | Result |
| --- | --- | --- | --- |
| G1: queries + 1,500 graded relevance labels | Exact files exist in frozen private GitHub: `data/electronics/query_validity/phase1_query_domain_validity_final_gt_v1.csv` and `data/electronics/relevance_qrels/phase3_relevance_final_qrels_v1.csv`. Prior direct public upload was safety-blocked; **do not circumvent**. | Approved publication, exact content/hash and correct query/grade counts; independently accessible public artifact | BLOCKED |
| G2: source playbook inputs for 50/830/1606 tracks | Four exact input JSONL files were recovered and validated locally; original playbook text includes email-like strings. | Exact frozen source, license/copyright preservation, targeted privacy/security review, reproducible public source retrieval or approved redistribution | BLOCKED |
| G3: full E5 + Guard scientific rerun | Original 4 input files pass exact SHA-256. Public CI only validates aggregate arithmetic/source-level tests, not original macOS MPS run. | Pinned E5 model revision, exact tokenizer/prefix/truncation, production execution code, Raw/Guard rankings and scores compared against frozen artifacts; note cross-backend differences | NOT EXECUTED |
| G4: provenance for historical 357-test audit | Paper/supplement report 357 pytest successes, 44 manifest JSON parses and 16 verifiable references, but contemporaneous test logs not found in GitHub. | Locate timestamped original run log and environment details, verify file sets and counts. Never substitute the public subset CI result. | NOT INDEPENDENTLY VERIFIED |
| G5: public tag / optional DOI | Curated public subset passes 53 CI tests but has unresolved disclosure and reproduction boundaries. | Reconcile manuscript Data Availability Statement; choose appropriate source/data licensing; author release approval; tag immutable curated package; archive/tag DOI if chosen | NOT ISSUED |

## Immediate next actions

1. Run the [four-input verification helper](../scripts/verify_recovered_inputs.py) locally or rely on the already documented dated match in [input-integrity report](RECOVERED_INPUT_INTEGRITY_AUDIT.md).
2. Address G1 publication approval and safety restrictions without attempting to bypass a refused upload.
3. Recover source playbook repository revision and confirm licensing and redaction approach for G2.
4. On source-compatible Mac, locate original P9/P11 357-test execution logs, together with original Python 3.10.13/MPS retrieval environment details.
5. Only after reproduction/availability wording is truthful and signed off, issue the **first citable release tag**. Zenodo DOI is optional and should match the real release.

## Missing or unverified does not mean failed science

This public artifact presently supports bounded consistency checks, not all claims of independent rerun. More data or testing may raise the level of reproducibility; neither a GitHub URL nor a citation alone supplies missing underlying artifacts.
