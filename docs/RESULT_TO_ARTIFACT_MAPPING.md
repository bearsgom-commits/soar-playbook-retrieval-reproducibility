# Result-to-artifact mapping (curated public subset)

This map links research claims to **actually published frozen aggregate** artifact files. It does not imply that the underlying per-query data, original model embeddings, or scientific pipeline are public or have been rerun.

| Claim or display | Published file(s) | Verification possible from this package |
| --- | --- | --- |
| Track B Raw, BM25, and Guard nDCG@10 | `results/electronics/human_gt/v1/scientific_results/track_b_utility_summary.json`, `track_b_noninferiority.json` | Exact reported aggregate means and retention decisions |
| Track B bootstrap noninferiority interval and study-specific 95% Raw-relative criterion | `.../track_b_noninferiority.json` | Consistency of stored CI, means and decision fields; **not** bootstrap resampling |
| B1 operational attribute coverage and available-case estimates | `.../track_b_omfr.json` | Stored denominators and 95% coverage-gate failure; exploratory interpretation only |
| Expanded Track C operational coverage and available-case estimates | `.../track_c_primary_omfr.json`, `.../track_c_broad_omfr.json` | Stored denominators and status; **no** Track C relevance-effectiveness validation |
| Six adjacent-ε ranking transition summaries | `results/electronics/ranking_propagation/v1/scientific_results/ranking_pair_summary.csv` | Stored transition counts, Top-1 changes, rank and overlap summary |
| Cross-seed robustness for fixed ε | `.../same_epsilon_seed_robustness.csv` | Stored per-track agreement summaries, not per-item ranking reconstruction |
| Retrieval and coverage plots' numeric data | `results/electronics/human_gt/v1/manuscript_v1/figure_source_data.json` | Cross-check numeric figure data against frozen aggregate JSON |
| Guard transformation source | `src/guard_repr.py` | Inspect control-to-dimension/bit mapping and transformation implementation |
| BM25 and relevant scoring helper semantics | `src/electronics/bm25_fixed.py`, `src/electronics/human_gt_scoring.py` | Inspect code and run selected unit tests |

**Note:** file names containing `track_b` in one row refer to full paths in the first column's directory, while those with `...` indicate the immediately preceding directory prefix. Use the repository browser for the exact files.

## Validation performed on the published subset

- **14 of 14** curated original files matched their pinned private source blob SHA-1 values.
- Structural numeric checks passed for published Raw/ε16 nDCG@10, noninferiority decision fields, three coverage fractions, and B1 adjacent Top-1 transition counts.
- A GitHub Actions curated-subset job ran **37 selected unit tests successfully** (not the private-research 357-test suite).
- The aggregate verifier cross-checks the numeric figure data against the frozen aggregate source JSON.
- Neither scientific reruns nor original reviewer participation are independently established by these checks.

## Interpretation and limitations

The study's 95% Raw-relative search-quality **noninferiority** is not equivalent to superiority over Raw. The 95% operational completeness threshold is not reached for B1, C-primary, or C-broad. Therefore available-case operational change estimates must not be presented as validated operational stability or as a certified jointly feasible operating region.

The public package should be cited as **partial supporting data and code**, not as a complete independent reproduction of the underlying encoder-and-retrieval experiment.
