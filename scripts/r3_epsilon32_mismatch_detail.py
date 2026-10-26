#!/usr/bin/env python3
"""R3-D read-only case diagnosis of epsilon=32 CPU anchor mismatches."""
from pathlib import Path
import sys,json,platform
import numpy as np
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference,SEEDS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def main():
 plan,_,_,_=prepare_inputs(Path(sys.argv[1]))
 out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 q=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 p=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 ref=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 cases=[]
 for seed in SEEDS:
  matrix=apply_guard_repr(q,32,seed)@apply_guard_repr(p,32,seed).T
  ranks=rank_top11(matrix,plan["query_ids"],plan["B0_anchor_ids"])
  for qid,top in ranks:
   expected=ref[(32,seed,qid)]["top_scored"]
   observed=[item[0] for item in top[:10]]
   frozen=[item["electronics_id"] for item in expected[:10]]
   if observed==frozen:continue
   scores={pid:float(matrix[plan["query_ids"].index(qid),i]) for i,pid in enumerate(plan["B0_anchor_ids"])}
   frozen_scores={x["electronics_id"]:float(x["score"]) for x in expected}
   union=sorted(set(observed)|set(frozen))
   case={"epsilon":32,"seed":seed,"query_id":qid,"same_top10_members":set(observed)==set(frozen),"top1_equal":observed[0]==frozen[0],"observed_top11":[{"id":pid,"score":val} for pid,val in top],"frozen_top11":expected,"observed_top10_ids":observed,"frozen_top10_ids":frozen,"score_diffs_for_common_frozen_ids":{pid: scores[pid]-frozen_scores[pid] for pid in union if pid in frozen_scores},"observed_rank10_rank11_margin":float(top[9][1]-top[10][1]),"frozen_rank10_rank11_margin":float(expected[9]["score"]-expected[10]["score"]) if len(expected)>10 else None}
   cases.append(case)
   print("MISMATCH",seed,qid,"MEMBERS_SAME",case["same_top10_members"],"TOP1_SAME",case["top1_equal"],"OBS_10_11_MARGIN",case["observed_rank10_rank11_margin"],flush=True)
 report={"track":"B0_anchor","epsilon":32,"device":"cpu","platform":platform.platform(),"mismatched_conditions":len(cases),"cases":cases}
 (out/"r3_detailed_mismatches.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("MISMATCH_COUNT=",len(cases),flush=True)
 print("STATUS="+("PASS_EXPECTED_THREE_CASES" if len(cases)==3 else "REVIEW_UNEXPECTED_CASE_COUNT"),flush=True)
if __name__=="__main__":main()
