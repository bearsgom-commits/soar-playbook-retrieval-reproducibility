#!/usr/bin/env python3
"""Recalculate B1 Guard nDCG@10 from published graded relevance qrels and Top-10 IDs.

Does not load the E5 encoder, read private annotations, or use frozen mean values
as an input to computation. Compares independent calculation with frozen means.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from electronics.human_gt_scoring import score_query_utility

EPS = (0, 2, 4, 8, 16, 32, 64)

def main():
    qpath=ROOT/"data/electronics/relevance_qrels/phase3_relevance_final_qrels_v1.csv"
    with qpath.open(encoding="utf-8", newline="") as f:
        rows=list(csv.DictReader(f))
    qrels=defaultdict(dict)
    for r in rows:
        key=r["query_id"]; doc=r["historical_playbook_id"]
        if doc in qrels[key]:
            raise AssertionError(("duplicate qrel", key, doc))
        qrels[key][doc]=int(r["relevance_grade"])
    assert len(rows)==1500 and len(qrels)==30 and all(len(x)==50 for x in qrels.values())
    covered={q for q,relevance in qrels.items() if any(grade>=2 for grade in relevance.values())}
    assert len(covered)==27, len(covered)

    stored=ROOT/"results/electronics/ranking_propagation/v1/source_rankings/B1_anchor_GUARD.jsonl"
    values=defaultdict(list)
    with stored.open(encoding="utf-8") as f:
        for line in f:
            row=json.loads(line)
            eps=int(row["epsilon"])
            ids=[x["electronics_id"] for x in row["top_scored"][:10]]
            result=score_query_utility(row["query_id"], ids, qrels)
            if row["query_id"] in covered:
                values[eps].append(result.ndcg_at_10)
    ref=json.loads((ROOT/"results/electronics/human_gt/v1/scientific_results/track_b_utility_summary.json").read_text(encoding="utf-8"))
    for eps in EPS:
        assert len(values[eps])==81, (eps,len(values[eps]))
        measured=sum(values[eps])/len(values[eps])
        expected=ref["covered"][f"GUARD_EPS_{eps}"]["ndcg_at_10"]
        assert abs(measured-expected)<1e-10, (eps,measured,expected)
        print(f"PASS eps={eps}: independently recomputed nDCG@10={measured:.9f}; frozen={expected:.9f}")
    print("PASS: 7 Guard retrieval-effectiveness means match 1500 public qrels and 630 frozen B1 rankings")
    print("NOTE: this is graded utility RECOMPUTATION FROM SAVED RANKINGS, not E5 model rerun.")

if __name__=="__main__":
    main()
