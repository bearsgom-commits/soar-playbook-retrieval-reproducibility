# Local Input Recovery for Full Scientific Replay

**Scope:** Identify frozen clean-text inputs that the original research manifest lists as **not Git-tracked**. No user-specific absolute paths or private file contents are included here.

Before running any scientific reproduction, the researcher must obtain the exact frozen input versions; do not reconstruct substitutes and silently call them the original data.

## Authoritative source-manifest references

The private source manifest named `manifests/electronics/E08_P0D_P5_P4_two_corpus_scientific_input_freeze_v1.json` (source commit `7c43a30511cd217cab6bfadf05db77b0c8ab943c`) records:

| Original artifact basename | Size (bytes) | Expected SHA-256 |
| --- | ---: | --- |
| `playbook_source_clean_inputs.jsonl` | 7,874,230 | `bafbf21b08f70de1355ea5bb985c4e57421fd35d56deb77b639dc4e168c94d89` |
| `query_source_clean_inputs.jsonl` | 12,226 | `e72be8067f94bf72c69d6cb69e9cbd3e431a8153e1c5ade468283fa9040c453c` |
| `anchor_50_clean_binding.jsonl` | 24,617 | `c404fea3d583a61932c0ca5a0c33212575acd5215468e8490367991c789f237b` |
| `token_lengths.jsonl` | 781,316 | `9732e3ba440d42397e09a629d648f4c4e573bcc8ef2aac6a0fe63d3b3e31c14a` |

The manifest also describes three Git-tracked corpus membership manifests (primary 830, broad 1606, source frame 1606). Those **membership metadata** are not substitutes for the complete text inputs.

## Non-destructive local search (macOS)

If the original audit directory still resides under `~/Downloads/research/_repro_audits`, search without changing files:

```bash
find ~/Downloads/research/_repro_audits -type f \( \
  -name 'playbook_source_clean_inputs.jsonl' -o \
  -name 'query_source_clean_inputs.jsonl' -o \
  -name 'anchor_50_clean_binding.jsonl' -o \
  -name 'token_lengths.jsonl' \
\) -print
```

For each found file, run `shasum -a 256 "FULL_FILE_PATH"` and compare with the appropriate expected value above. Preserve the exact file unmodified. Make a separately reviewed copy only after authorizing redistribution and screening for secrets, copyrighted content, and personal data.

Do not commit private local folders, full experimental logs, or the source directory history to this public repository.

## Next gates if the files are recovered

1. Independently verify all SHA-256 and expected sizes.
2. Resolve source license, annotator privacy, and any operational sensitivity.
3. Recover the original Python 3.10.13/macOS MPS scientific setup and exact model revision.
4. Run an isolated, first-principles E5 encoding and Guard retrieval experiment without modifying frozen results.
5. Compare full rankings, metrics and figure values against the frozen results; report CPU/MPS deviations.
6. Release only the data and execution outputs lawfully approved for disclosure, with a truthful availability statement.

**Current status: RECOVERY_INSTRUCTIONS_CREATED; LOCAL_FILES_NOT_VERIFIED in the current environment.**
