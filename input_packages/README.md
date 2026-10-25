# Author-approved frozen-input bundle

Place the ZIP named `SOAR_FROZEN_INPUTS_AUTHOR_APPROVED_20261025.zip` in this folder. Its four original source JSONL files have SHA-256 checks registered in `scripts/verify_recovered_inputs.py`.

The GitHub Actions `Model-pinned E5 Guard reproduction` workflow is configured to run upon this exact path being added. It will not silently change or overwrite frozen source artifacts. The bundle includes upstream playbook-derived text and an exact upstream MIT notice; keep licensing and source attribution intact.

Avoid uploading other private folders, reviewer identification records, tokens, or unreviewed source data.
