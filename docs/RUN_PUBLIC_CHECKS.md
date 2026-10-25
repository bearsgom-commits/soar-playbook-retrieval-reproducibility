# Commands for the published subset

## Available now

To run the independent published-aggregate consistency checker:

```bash
python scripts/verify_public_aggregates.py
```

To run only the available **source-level unit tests**, first install the testing dependencies and then run:

```bash
python -m pip install -r requirements-public.txt
PYTHONPATH=src python -m pytest -q \
  tests/test_electronics_bm25_fixed.py \
  tests/test_electronics_human_gt_scoring.py
```

These commands exercise the **curated subset only**. Their success must not be reported as an execution of the complete original research experiment or a verification of the 357-test private-environment report.

## Not yet supplied

- A complete environment lockfile for the original macOS MPS scientific run;
- Full query and playbook input snapshots and their redistribution permissions;
- Encoder invocation, Guard retrieval production runner, and full frozen rank inputs;
- Individual evaluation provenance, grade-by-query data and full bootstrap recomputation.

For reproducibility claim scope and source commit identities, see [Artifact provenance and verification scope](ARTIFACT_PROVENANCE.md).
