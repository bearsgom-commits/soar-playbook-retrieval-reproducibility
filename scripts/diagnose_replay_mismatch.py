#!/usr/bin/env python3
"""Read-only diagnosis of MPS rerun versus pinned published ranking artifacts."""
from collections import defaultdict
from pathlib import Path
from statistics import mean
import json
import argparse

EPS = (0, 2, 4, 8, 16, 32, 64)
SEEDS = (7, 13, 42)
TRACKS = ("B0_anchor", "B1_anchor", "C_primary", "C_broad")

def read(path):
    result = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        x = json.loads(raw)
        k = (int(x["epsilon"]), int(x["seed"]), x["query_id"])
        if k in result:
            raise ValueError(("Duplicate row", path, k))
        result[k] = x["top_scored"]
    return result

def compare(original, regenerated):
    ids0 = [z["electronics_id"] for z in original[:10]]
    ids1 = [z["electronics_id"] for z in regenerated[:10]]
    o_scores={z["electronics_id"]:float(z["score"]) for z in original[:11]}
    n_scores={z["electronics_id"]:float(z["score"]) for z in regenerated[:11]}
    common=set(o_scores)&set(n_scores)
    diffs=[abs(o_scores[x]-n_scores[x]) for x in common]
    return {
        "top1_agree":int(ids0[0]==ids1[0]),
        "top10_exact":int(ids0==ids1),
        "top10_overlap":len(set(ids0)&set(ids1))/10,
        "top11_common":len(common),
        "common_score_abs_mean":mean(diffs) if diffs else None,
        "common_score_abs_max":max(diffs) if diffs else None,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fresh",type=Path,required=True)
    ap.add_argument("--reference",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    evidence={}
    for track in TRACKS:
        f=read(a.fresh/(track+"_GUARD_fresh.jsonl"))
        r=read(a.reference/(track+"_GUARD.jsonl"))
        if set(f)!=set(r):
            raise ValueError(f"MISSING_OR_EXTRA_RANKS:{track}, fresh={len(f)}, reference={len(r)}")
        summary={}
        for e in EPS:
            vals=[compare(r[(e,s,f"Q{q:02d}")],f[(e,s,f"Q{q:02d}")]) for s in SEEDS for q in range(1,31)]
            summary[str(e)]={
                "count":len(vals),
                "top1_match":sum(z["top1_agree"] for z in vals),
                "exact_top10":sum(z["top10_exact"] for z in vals),
                "mean_top10_overlap":mean(z["top10_overlap"] for z in vals),
                "mean_top11_common":mean(z["top11_common"] for z in vals),
                "mean_common_score_difference":mean(z["common_score_abs_mean"] for z in vals if z["common_score_abs_mean"] is not None) if any(z["common_score_abs_mean"] is not None for z in vals) else None,
            }
        example=(0,7,"Q01")
        summary["example"]={"condition":str(example),"frozen":r[example][:3],"fresh":f[example][:3]}
        evidence[track]=summary
        print(f"TRACK={track}")
        for e in EPS:
            row=summary[str(e)]
            print(f" EPS={e:2} top1={row['top1_match']}/90, top10={row['exact_top10']}/90, mean_overlap={row['mean_top10_overlap']:.4f}, mean_common_score_delta={row['mean_common_score_difference']}")
        print(f" EXAMPLE {example}: frozen_top3={[x['electronics_id'] for x in r[example][:3]]}, fresh_top3={[x['electronics_id'] for x in f[example][:3]]}")
    a.output.write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"REPORT={a.output}")
    print("CAUTION: diagnostics identify observed differences, not isolated causal mechanism.")

if __name__ == "__main__":
    main()
