#!/usr/bin/env python3
"""R5 finite audit of R4 evidence; never modifies frozen references."""
import argparse,json,hashlib,platform
from pathlib import Path
TRACKS=("B0_anchor","B1_anchor","C_primary","C_broad")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def rows(p):
 result={}
 for line in p.read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  d=json.loads(line)
  key=(int(d["epsilon"]),int(d["seed"]),d["query_id"])
  if key in result:raise ValueError(f"DUPLICATE:{p}:{key}")
  result[key]=d
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--r4",type=Path,required=True);p.add_argument("--reference",type=Path,default=Path("results/electronics/ranking_propagation/v1/source_rankings"));p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 a.out.mkdir(parents=True)
 raw=json.loads((a.r4/"comparison_report.json").read_text())
 if raw["device"]!="cpu":raise ValueError("R4_EXPECTED_CPU")
 results={"scope":"R4 independently reproduced CPU output vs immutable frozen Guard ranks","environment":platform.platform(),
          "source_backend_warning":"CPU is not a proof of MPS numerical identity",
          "r4_report_sha":sha(a.r4/"comparison_report.json"),"tracks":{},"all_cases":[]}
 t10=t1=0
 for track in TRACKS:
  fresh_path=a.r4/f"{track}_GUARD_fresh.jsonl"
  ref_path=a.reference/f"{track}_GUARD.jsonl"
  fresh,frozen=rows(fresh_path),rows(ref_path)
  if set(fresh)!=set(frozen) or len(fresh)!=630:raise ValueError(f"CONDITION_KEY_DRIFT:{track}")
  cases=[];top10=top1=0;members_equal_count=0
  for key in sorted(fresh):
   ob=fresh[key]["top_scored"];ex=frozen[key]["top_scored"]
   oi=[x["electronics_id"] for x in ob[:10]];ei=[x["electronics_id"] for x in ex[:10]]
   same=oi==ei;top10+=same;top1+=oi[0]==ei[0]
   if same:continue
   members=set(oi)==set(ei);members_equal_count+=members
   common=set(oi)&set(ei)
   exscores={x["electronics_id"]:float(x["score"]) for x in ex}
   obscores={x["electronics_id"]:float(x["score"]) for x in ob}
   score_delta=max((abs(obscores[i]-exscores[i]) for i in common),default=None)
   item={"track":track,"epsilon":key[0],"seed":key[1],"query_id":key[2],
         "top1_equal":oi[0]==ei[0],"members_equal":members,
         "top10_observed":oi,"top10_frozen":ei,
         "common_max_abs_score_diff":score_delta,
         "observed_top1_margin":float(ob[0]["score"])-float(ob[1]["score"]),
         "frozen_top1_margin":float(ex[0]["score"])-float(ex[1]["score"])}
   cases.append(item);results["all_cases"].append(item)
  reported=raw["track_result"][track]
  if (top10,top1)!=(reported["top10_exact"],reported["top1_exact"]):raise ValueError(f"REPORT_CONSISTENCY_FAIL:{track}")
  results["tracks"][track]={"total":630,"top10_exact":top10,"top1_exact":top1,
    "mismatch_count":len(cases),"same_members_but_order_different":members_equal_count,
    "fresh_sha":sha(fresh_path),"frozen_sha":sha(ref_path),"cases":cases}
  t10+=top10;t1+=top1
 results["total_conditions"]=2520;results["top10_exact"]=t10;results["top1_exact"]=t1
 results["strict_rank_reproducibility_pass"]=t10==2520
 results["final_claim"]="CPU exact Top10 fails" if t10!=2520 else "CPU exact Top10 passes; MPS still independently scoped"
 (a.out/"r5_audit.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
 md=["# R5 independent audit of R4", "",f"- CPU Top-10: **{t10}/2520**",f"- CPU Top-1: **{t1}/2520**",
     f"- Strict Top-10 PASS: **{t10==2520}**","- Frozen references untouched","- MPS equivalence **not established**","","## Mismatched conditions"]
 for c in results["all_cases"]:
  md.append(f"- {c['track']} ε={c['epsilon']} seed={c['seed']} {c['query_id']} Top1_same={c['top1_equal']} members_same={c['members_equal']} common_score_delta={c['common_max_abs_score_diff']}")
 (a.out/"r5_audit.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("R5_TOP10=",t10,"/2520 R5_TOP1=",t1,"/2520")
 print("R5_MISMATCH_COUNT=",len(results["all_cases"]))
 print("R5_TOP1_MISMATCH_CASES=",[(c["track"],c["epsilon"],c["seed"],c["query_id"]) for c in results["all_cases"] if not c["top1_equal"]])
 print("STATUS=R5_AUDIT_COMPLETED_STRICT_PASS_"+str(t10==2520).upper())
 print("R5_REPORT=",a.out/"r5_audit.md")
if __name__=="__main__":main()
