#!/usr/bin/env python3
"""R3-J: deterministic CPU control with per-stage quantization boundary evidence."""
from pathlib import Path
import hashlib,json,os,platform,sys
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from threadpoolctl import threadpool_info
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,SEEDS,rank_top11,load_reference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr,l2_normalize,make_projection_matrix,eps_to_repr_spec,uniform_quantize

def sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def main():
 torch.set_num_threads(1)
 torch.set_num_interop_threads(1)
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 out.mkdir(parents=True,exist_ok=False)
 plan,_,_,_=prepare_inputs(base)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 q=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 p=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 ref=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 report={"platform":platform.platform(),"torch":torch.__version__,"threads":torch.get_num_threads(),"threadpools":threadpool_info(),"q_sha":sha(q),"p_sha":sha(p),"cases":{}}
 for seed in SEEDS:
  w=make_projection_matrix(768,320,seed)
  qn=l2_normalize(q);pn=l2_normalize(p)
  qp=qn@w;pp=pn@w
  qscaled=(np.clip(qp,-1,1)+1)*(1023/2)
  pscaled=(np.clip(pp,-1,1)+1)*(1023/2)
  q_margin=np.abs(qscaled-np.floor(qscaled)-0.5)
  p_margin=np.abs(pscaled-np.floor(pscaled)-0.5)
  qg=apply_guard_repr(q,32,seed);pg=apply_guard_repr(p,32,seed)
  scores=qg@pg.T
  ranks=rank_top11(scores,plan["query_ids"],plan["B0_anchor_ids"])
  mismatches=[]
  for qid,top in ranks:
   f=ref[(32,seed,qid)]["top_scored"]
   ids=[id for id,_ in top[:10]]
   exp=[z["electronics_id"] for z in f[:10]]
   if ids!=exp:
    mismatches.append({"qid":qid,"top1_equal":ids[0]==exp[0],"members_equal":set(ids)==set(exp),"frozen_ids":exp,"replayed_ids":ids,"observed_top11":top,"frozen_top11":f})
  report["cases"][str(seed)]={"projection_w_sha":sha(w),"q_norm_sha":sha(qn),"p_norm_sha":sha(pn),"q_project_sha":sha(qp),"p_project_sha":sha(pp),"q_quantize_margin_min":float(q_margin.min()),"p_quantize_margin_min":float(p_margin.min()),"q_quantize_near_1e_5":int((q_margin<1e-5).sum()),"p_quantize_near_1e_5":int((p_margin<1e-5).sum()),"q_guard_sha":sha(qg),"p_guard_sha":sha(pg),"score_sha":sha(scores),"mismatches":mismatches}
  print("SEED",seed,"Q_PROJ",sha(qp),"P_PROJ",sha(pp),"QG",sha(qg),"PG",sha(pg),"SCORE",sha(scores),"MISMATCHES",[x["qid"] for x in mismatches],flush=True)
 (out/"r3j_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("STATUS=R3J_EVIDENCE_SAVED_NOT_FULL_REPRODUCTION_PASS",flush=True)
if __name__=="__main__":main()
