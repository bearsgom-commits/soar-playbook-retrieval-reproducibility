# Upstream Cortex XSOAR content: licensing review

**Initial finding:** The publicly accessible [demisto/content](https://github.com/demisto/content) repository identifies itself as a Cortex XSOAR community content source and publishes an [MIT license](https://github.com/demisto/content/blob/master/LICENSE). The official [Cortex XSOAR development documentation](https://xsoar.pan.dev/docs/contributing/contributing) likewise identifies that content repository as MIT-licensed.

**Interpretation:** The MIT license permits redistribution of source material covered by that license, provided required copyright and license notices are preserved. This finding alone is **not** approval to redistribute every file from a mixed research corpus; provenance, actual per-file rights, source revision, author-supplied additions, and any relevant license exceptions must be checked.

## Provenance evidence in private research source

- The conference anchor dataset's `source_file` paths refer to upstream `Packs/.../Playbooks/*.yml` files.
- The expanded source-frame contains **1,606** manifest members and records `electronics_id` and per-item `source_sha256`.
- The **830** primary playbooks are a machine-selected subset, not an independently human-reviewed ground-truth sample.
- The source repository's frozen experimental manifest shows the expanded clean playbook input JSONL was not a tracked file. Do not presume it is downloadable from this public GitHub repository.

## Outstanding rights and fidelity verification

- [ ] Recover and verify the **exact upstream source commit** for the original frozen playbook checkout.
- [ ] Check that all included raw playbooks derive from the MIT-covered `demisto/content` tree and that no external or differently licensed packs were mixed in.
- [ ] Retain copyright notices and the complete MIT license alongside any copies or substantial derived extracts.
- [ ] Compare the regenerated 50/830/1606 source texts' hashes with the frozen private input-binding manifests.
- [ ] Verify the research-derived dataset contains no proprietary enrichment or personally identifying content.
- [ ] Decide whether publication should provide an upstream-pinned downloader/transform script instead of republishing all YAML content.

**Status:** UPSTREAM_LICENSE_IDENTIFIED; PRECISE_CORPUS_REDISTRIBUTION_NOT_YET_APPROVED.

The absence of a full data bundle here is a provenance/verification gap, not a claim that a publisher or platform prohibited all redistribution.
