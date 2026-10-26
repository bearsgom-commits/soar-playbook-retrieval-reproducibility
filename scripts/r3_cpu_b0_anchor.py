#!/usr/bin/env python3
"""R3: independent CPU B0 anchor control, 30 queries and 50 playbooks only."""
from pathlib import Path
import sys,json,platform,hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,EPS,SEEDS,rank_top11,load_reference,compare_guard
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def main():
 plan,_,_,_=prepare_inputs(Path(sys.argv[1]))
 out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 q=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 p=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 assert q.shape==(30,768) and p.shape==(50,768)
 assert q.dtype==np.float32 and p.dtype==np.float32
 refroot=Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings"
 ref=load_reference(refroot/"B0_anchor_GUARD.jsonl")
 summary={"track":"B0_anchor","device":"cpu","platform":platform.platform(),"query_count":30,"playbook_count":50,"conditions":630,"top10_exact":0,"top1_exact":0,"max_common_score_difference":0.0,"per_epsilon":{}}
 for eps in EPS:
  t10=t1=0;d=0
  for seed in SEEDS:
   matrix=apply_guard_repr(q,eps,seed)@apply_guard_repr(p,eps,seed).T
   ranks=rank_top11(matrix,plan["query_ids"],plan["B0_anchor_ids"])
   n10,n1,err=compare_guard("B0_anchor",eps,seed,ranks,ref)
   t10+=n10;t1+=n1;d=max(d,err)
  summary["per_epsilon"][str(eps)]={"top10_exact":t10,"top1_exact":t1,"total":90,"max_diff":d}
  summary["top10_exact"]+=t10;summary["top1_exact"]+=t1
  summary["max_common_score_difference"]=max(d,summary["max_common_score_difference"])
  print(f"EPS={eps} TOP10={t10}/90 TOP1={t1}/90 MAX_COMMON_SCORE_DIFF={d}",flush=True)
 summary["pass_exact"]=summary["top10_exact"]==630
 (out/"r3_cpu_anchor.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
 print("R3_TOP10_EXACT=",summary["top10_exact"],"/630",flush=True)
 print("R3_TOP1_EXACT=",summary["top1_exact"],"/630",flush=True)
 print("STATUS=" + ("PASS_R3_CPU_B0" if summary["pass_exact"] else "FAIL_R3_CPU_B0"),flush=True)
if __name__=="__main__":main()
