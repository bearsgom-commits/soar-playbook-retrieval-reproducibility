#!/usr/bin/env python3
"""C1: read-only forensic audit of mismatching R4 ranked candidates."""
import argparse,collections,json,math
from pathlib import Path
def load(p):
 d={}
 for line in p.read_text().splitlines():
  if not line.strip():continue
  x=json.loads(line);k=(int(x["epsilon"]),int(x["seed"]),x["query_id"])
  if k in d:raise RuntimeError("duplicate "+str(k))
  d[k]=x
 return d
def inversion(a,b):
 pos={v:i for i,v in enumerate(b)}
 common=[v for v in a if v in pos]
 return [(x,y) for i,x in enumerate(common) for y in common[i+1:] if pos[x]>pos[y]]
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--r4",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 a.out.mkdir(parents=True)
 report={"method":"R4 rank 11 records against frozen rank 11; no model rerun","cases":[],"by_track":{}}
 root=Path("results/electronics/ranking_propagation/v1/source_rankings")
 for track in ["B0_anchor","B1_anchor","C_primary","C_broad"]:
  obs=load(a.r4/(track+"_GUARD_fresh.jsonl"));frozen=load(root/(track+"_GUARD.jsonl"))
  assert set(obs)==set(frozen) and len(obs)==630
  for (eps,seed,qid),v in sorted(obs.items()):
   o=v["top_scored"];f=frozen[(eps,seed,qid)]["top_scored"]
   a_ids=[x["electronics_id"] for x in o[:10]];b_ids=[x["electronics_id"] for x in f[:10]]
   if a_ids==b_ids:continue
   os={x["electronics_id"]:float(x["score"]) for x in o}
   fs={x["electronics_id"]:float(x["score"]) for x in f}
   shared=set(os)&set(fs)
   inversions=inversion(a_ids,b_ids)
   swaps=[]
   for x,y in inversions:
    if x not in os or y not in os or x not in fs or y not in fs:continue
    swaps.append({"a":x,"b":y,
                  "observed_score_gap":os[x]-os[y],
                  "frozen_score_gap":fs[x]-fs[y],
                  "score_gap_change":(os[x]-os[y])-(fs[x]-fs[y])})
   c={"track":track,"epsilon":eps,"seed":seed,"query_id":qid,
      "top1_changed":a_ids[0]!=b_ids[0],
      "same_top10_members":set(a_ids)==set(b_ids),
      "observed_only":sorted(set(a_ids)-set(b_ids)),
      "frozen_only":sorted(set(b_ids)-set(a_ids)),
      "inversion_count":len(inversions),
      "inversion_pairs":swaps,
      "observed_top1_gap":os[a_ids[0]]-os[a_ids[1]],
      "frozen_top1_gap":fs[b_ids[0]]-fs[b_ids[1]],
      "max_common_score_delta":max(abs(os[z]-fs[z]) for z in shared),
      "score_delta_by_id":{z:os[z]-fs[z] for z in sorted(shared)},
      "observed_top11":o,"frozen_top11":f}
   report["cases"].append(c)
 by=collections.defaultdict(list)
 for c in report["cases"]:by[c["track"]].append(c)
 report["by_track"]={k:{"mismatches":len(v),"top1_changes":sum(x["top1_changed"] for x in v),
                                "set_changes":sum(not x["same_top10_members"] for x in v)} for k,v in by.items()}
 assert len(report["cases"])==14,"Unexpected R4 mismatch count"
 assert sum(x["top1_changed"] for x in report["cases"])==1,"Unexpected top1 count"
 (a.out/"c1_forensic.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
 print("C1_TOTAL_MISMATCHES=",len(report["cases"]))
 print("C1_TRACK_SUMMARY=",report["by_track"])
 for c in report["cases"]:
  print("C1_CASE",c["track"],"eps",c["epsilon"],"seed",c["seed"],c["query_id"],
        "TOP1_CHANGED",c["top1_changed"],"SAME_MEMBERS",c["same_top10_members"],
        "INVERSIONS",c["inversion_count"],"MAX_COMMON_SCORE_DIFF",c["max_common_score_delta"])
  if c["top1_changed"]:
   print("C1_TOP1_FORENSICS=",json.dumps(c,ensure_ascii=False))
 print("STATUS=C1_EVIDENCE_CLASSIFIED_CAUSAL_SOURCE_NOT_YET_PROVEN")
if __name__=="__main__":main()
