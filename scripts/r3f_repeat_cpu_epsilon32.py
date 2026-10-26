#!/usr/bin/env python3
"""R3-F: repeat complete CPU B0 eps32 computation, report drift and frozen mismatches."""
from pathlib import Path
import sys,json,hashlib,platform
import numpy as np
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference,SEEDS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
 plan,_,_,_=prepare_inputs(Path(sys.argv[1]))
 dest=Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
 ref=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 report={"platform":platform.platform(),"model":MODEL_ID,"revision":MODEL_REV,"device":"cpu","batch_size":16,"epsilon":32,"repetitions":[]}
 for iteration in range(1,4):
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
  q=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
  p=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
  rep={"iteration":iteration,"query_sha256":sha(q),"anchor_sha256":sha(p),"seeds":{}}
  for seed in SEEDS:
   m=apply_guard_repr(q,32,seed)@apply_guard_repr(p,32,seed).T
   found=rank_top11(m,plan["query_ids"],plan["B0_anchor_ids"])
   mismatches=[]
   for qid,top in found:
    reference=ref[(32,seed,qid)]["top_scored"]
    original=[r["electronics_id"] for r in reference[:10]]
    observed=[pid for pid,_ in top[:10]]
    if original!=observed:
     mismatches.append({"qid":qid,"same_members":set(original)==set(observed),"same_top1":original[0]==observed[0],"frozen_top10":original,"observed_top10":observed,"observed_10_11_margin":float(top[9][1]-top[10][1])})
   rep["seeds"][str(seed)]={"score_matrix_sha256":sha(m),"mismatches":mismatches,"mismatch_count":len(mismatches)}
  report["repetitions"].append(rep)
  print("ITERATION",iteration,"Q_SHA",rep["query_sha256"],"P_SHA",rep["anchor_sha256"],"MISMATCHES",{s:d["mismatch_count"] for s,d in rep["seeds"].items()},flush=True)
  del model
 keys=[(r["query_sha256"],r["anchor_sha256"],tuple(r["seeds"][str(s)]["score_matrix_sha256"] for s in SEEDS)) for r in report["repetitions"]]
 report["repeat_byte_identical"]=len(set(keys))==1
 report["mismatches_per_iteration"]=[sum(v["mismatch_count"] for v in r["seeds"].values()) for r in report["repetitions"]]
 (dest/"r3f_repeat_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("REPEAT_BYTE_IDENTICAL=",report["repeat_byte_identical"],flush=True)
 print("MISMATCHES_PER_ITERATION=",report["mismatches_per_iteration"],flush=True)
 print("STATUS=PASS_R3F_DIAGNOSTIC_EXECUTION",flush=True)
if __name__=="__main__":main()
