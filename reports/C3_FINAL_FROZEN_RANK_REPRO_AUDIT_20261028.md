# C3 final frozen-ranking reproducibility audit (2026-10-28)

## Evidence and immutable scope

- Repository: `bearsgom-commits/soar-playbook-retrieval-reproducibility`
- B0 GitHub Actions run: https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility/actions/runs/40505643422
- Remaining-tracks run: https://github.com/bearsgom-commits/soar-playbook-retrieval-reproducibility/actions/runs/40507189963
- B0 artifact ID: `12735625852` (summary and all-conditions JSONL).
- Remaining-tracks artifact ID: `12751434312` (summary and all-conditions JSONL).
- Four frozen input hashes validated by `prepare_inputs`. Frozen rankings read-only.
- `intfloat/multilingual-e5-base` revision `d128750597153bb5987e10b1c3493a34e5a4502a`.
- Corrective implementation: GitHub macOS MPS PyTorch 2.10.0; replace all 73 E5 `nn.Linear` forward operations with per-token `torch.mv` vector multiplication, leaving pretrained weights unchanged; Guard and deterministic f32 dot/ranking read from existing research source.
- This is an *alternative controlled execution path*, not proof of identical hardware/software behavior to original source environment.

## Verified outcomes (all 2520 combinations)

| Track | Top10 exact | Top1 exact | Top10 mismatches |
|---|---:|---:|---:|
| B0_anchor | 630/630 | 630/630 | 0 |
| B1_anchor | 628/630 | 630/630 | 2 |
| C_primary | 627/630 | 630/630 | 3 |
| C_broad | 627/630 | 630/630 | 3 |
| **Total** | **2512/2520 (99.6825%)** | **2520/2520 (100%)** | **8** |

Mismatch breakdown: 5 same Top-10 members but altered order; 3 changed membership. No Top-1 changes.

| Track | ε | Seed | Query | Difference |
|---|---:|---:|---|---|
| B1_anchor | 32 | 7 | Q17 | membership |
| B1_anchor | 32 | 13 | Q28 | order |
| C_primary | 16 | 42 | Q24 | order |
| C_primary | 32 | 13 | Q28 | membership |
| C_primary | 32 | 42 | Q27 | order |
| C_broad | 2 | 13 | Q11 | membership |
| C_broad | 16 | 42 | Q24 | order |
| C_broad | 32 | 42 | Q27 | order |

## Interpretation / gates

- **PASS:** immutable-source input integrity checks, corrected-MPS B0 630/630 exact Top10 and Top1.
- **PASS:** all-tracks Top1 exact 2520/2520.
- **NOT PASS:** complete four-track exact Top10 2520/2520; measured 2512/2520.
- Complete replication must not be claimed. Residual 8 cases are recorded as limitations.
- The change from conventional MPS `F.linear` to per-token `torch.mv` dramatically reduced Q01 CPU-MPS embedding error (0.07232995 to 2.086e-7); it is a reproducibility *workaround* not proof of an upstream PyTorch defect.
- The observed rank agreement does not independently revalidate labels, human evaluation, utility/OMFR/security calculations, or research conclusions outside these 2520 retrieval-ranking cases.
- Runtime in remaining-tracks summary 14802 seconds (~4h 7m). No computational rerun is justified solely to pursue eight remaining near-boundary mismatches.

## Completion declaration

**Status: COMPLETED_WITH_EIGHT_TOP10_MISMATCHES**. Frozen-rank verification is finished at the predeclared exhaustive condition scope. The strict full Top10 gate remains FAIL; the Top1 gate is PASS. Publish or cite the above exact rates and retain original evidence artifacts. Further work is optional and must be motivated by a scientific need for exact Top10, not by a claim that the pipeline is unverified.
