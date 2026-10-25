# Full model rerun — data-publication handoff

**As of 2026-10-25:** The first-party E5/Guard scientific rerun is **prepared but has not run on the full frozen corpus**. It must not be substituted with the successful frozen-ranking or aggregate checks.

## Already in the public repository

- 30 query validity records, 1,500 graded relevance judgments; exact frozen source Git blobs.
- Primary 830 and broad 1,606 playbook membership manifests.
- Four frozen Guard ranking inputs (B0, B1, C-primary, C-broad), 630 query/configuration rows each.
- Exact original encoder input contract: `src/electronics/encoder_runner.py`.
- Reproducibility driver: `scripts/rerun_e5_guard_from_frozen_inputs.py`.
- Recorded dependencies: `requirements-replay.txt`.
- GitHub Actions workflow: `.github/workflows/e5-guard-source-replay.yml`.
- MIT notice for the pinned public Cortex XSOAR content revision in `third_party/demisto-content-LICENSE.txt`.

## Exact-input archive upload required

The author-approved, SHA-256-verified archive is named:

`SOAR_FROZEN_INPUTS_AUTHOR_APPROVED_20261025.zip`

Package SHA-256:

`cbc1b592601ebd490e64f64206df0d2b39ace9b5d5a7e5d037bf65c389318720`

The archive contains 4 exact original JSONL inputs (1,606 playbooks; 30 queries; 50 anchor IDs; 1,766 tokenizer records), a separately identified deterministic derived 830-primary subset, source-origin notes and the upstream license.

**Publish** to this exact GitHub path, unmodified:

`input_packages/SOAR_FROZEN_INPUTS_AUTHOR_APPROVED_20261025.zip`

After the file is committed to the `main` branch, the workflow [Model-pinned E5 Guard reproduction](../.github/workflows/e5-guard-source-replay.yml) is configured to trigger automatically.

**Public release implication:** that ZIP contains actual search-input text extracted from upstream playbooks, including some public-source email-like strings. By putting it in a public Git repository, its content becomes accessible to others and remains in Git history. Source files are derived from the pinned MIT-licensed upstream project; preserve the included copyright/license notice.

## What the workflow must actually do

1. Verify all four original file SHA-256 values and their B0/B1 binding.
2. Install the recorded Python 3.10 family and frozen model dependencies on an Apple MPS runner.
3. Fetch the exact E5 model revision `d128750597153bb5987e10b1c3493a34e5a4502a` (and validate the pinned snapshot).
4. Encode four original input arrays: C queries (30), C broad playbooks (1606), B0 queries (30), B0 anchors (50).
5. Create B1 and 830-primary embeddings strictly as **views** of the frozen C-broad representation.
6. Generate fresh Raw and all 7 ε × 3 seed Guard rankings across all four tracks into a new output folder.
7. Compare Guard Top-10 order and Top-1 selection against the frozen published reference rankings (630 conditions for each track).
8. Save comparison report and outputs as GitHub Actions artifacts.
9. Fail the execution if exact MPS Guard Top-10 agreement is not achieved; do **not** modify scientific parameters to manufacture a pass.

## Scientific interpretation

- The historical source environment used Python 3.10.13/macOS MPS; the hosted preflight runner used Python **3.10.11**. It is **not** an identical environment, even when other packages match.
- Full end-to-end verification cannot be claimed until the actual encoder/retrieval job executes and the saved report is reviewed.
- Four public Guard reference rank files are present; frozen original Raw ranking detail per track is **not** part of this public package, so Raw exact reproduction remains a separate evidence gate.
- Public qrels + B1 frozen Guard ranks yielded exact numeric agreement for seven Guard nDCG@10 means. That is metric-level reproduction from saved results, not a new E5 inference.
- A previous preflight failed because newer libraries did not populate the private model `_commit_hash`; the source model snapshot's immutable revision is now independently checked. This is a verifier adjustment, **not** a change in the E5 model revision.

## Local source-compatible alternative

On the researcher's original Mac, install the recorded dependencies, keep all original JSONL files in a private directory and run:

```bash
python -m pip install -r requirements-replay.txt
python scripts/rerun_e5_guard_from_frozen_inputs.py \
  --inputs /path/to/four/original/jsonl/files \
  --device mps --batch-size 4 \
  --out /path/to/new_empty_results_directory
```

Always keep the original archived results read-only. Preserve complete logs, the report and exact model/environment versions.

**No DOI or final release tag should be assigned to a claimed full reproduction before the workflow succeeds and output is audited.**
