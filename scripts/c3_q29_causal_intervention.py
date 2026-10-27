#!/usr/bin/env python3
"""C3 targeted causal intervention: preserve original algorithm and frozen outputs."""
import json,sys,hashlib,platform
from pathlib import Path
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr,l2_normalize,make_projection_matrix,uniform_quantize
def hasharray(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def stages(p,seed):
 w=make_projection_matrix(768,320,seed)
 n=l2_normalize(p)
 pr=n@w
 qu=uniform_quantize(pr,10)
 return pr,qu,l2_normalize(qu)
def main():
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 torch.set_num_threads(1)
 torch.set_num_interop_threads(1)
 plan,_,_,_=prepare_inputs(base)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 q=model.encode(plan["arrays"]["B0_query"],batch_size=16,normalize_embeddings=True,convert_to_numpy=True,prompt="",show_progress_bar=False)
 p16=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,normalize_embeddings=True,convert_to_numpy=True,prompt="",show_progress_bar=False)
 p1=model.encode(plan["arrays"]["B0_anchor"],batch_size=1,normalize_embeddings=True,convert_to_numpy=True,prompt="",show_progress_bar=False)
 ids=plan["B0_anchor_ids"];qid="Q29";qi=plan["query_ids"].index(qid);seed=7
 frozen=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")[(32,seed,qid)]["top_scored"]
 qg=apply_guard_repr(q,32,seed);pr16,quant16,g16=stages(p16,seed);pr1,quant1,g1=stages(p1,seed)
 score16=qg@g16.T;score1=qg@g1.T
 def ordering(score):
  found=rank_top11(score,plan["query_ids"],ids)
  top=dict(found)[qid]
  return [x[0] for x in top],{id:float(score[qi,k]) for k,id in enumerate(ids)}
 order16,s16=ordering(score16);order1,s1=ordering(score1)
 diff=np.argwhere(quant16!=quant1)
 changed=[{"playbook_id":ids[int(i)],"playbook_row":int(i),"coordinate":int(j),
  "projected_batch16":float(pr16[i,j]),"projected_batch1":float(pr1[i,j]),
  "quant_batch16":float(quant16[i,j]),"quant_batch1":float(quant1[i,j])} for i,j in diff]
 def margin(scores):return scores["XPB018"]-scores["XPB027"]
 delta={id:float(s1[id]-s16[id]) for id in ids if s1[id]!=s16[id]}
 frozen_scores={x["electronics_id"]:float(x["score"]) for x in frozen}
 v={"environment":{"platform":platform.platform(),"torch":torch.__version__,"threads":torch.get_num_threads()},
   "q_sha":hasharray(q),"p16_sha":hasharray(p16),"p1_sha":hasharray(p1),
   "qg_sha":hasharray(qg),"guard_p16_sha":hasharray(g16),"guard_p1_sha":hasharray(g1),
   "quantization_changed_coordinates":changed,
   "batch16_top11_ids":order16,"batch1_top11_ids":order1,
   "frozen_top11_ids":[x["electronics_id"] for x in frozen],
   "batch16_top1":order16[0],"batch1_top1":order1[0],
   "score_gap_XPB018_minus_XPB027":{"frozen":margin(frozen_scores),"batch16":margin(s16),"batch1":margin(s1)},
   "score_changes_caused_by_batch_change":delta,
   "causal_test_bound":"Only tests changing batch size and effect on guarded ranking on one runner; cannot prove cross-machine causal attribution."}
 (out/"c3_cpu_intervention.json").write_text(json.dumps(v,indent=2,ensure_ascii=False))
 print("C3_P16_SHA=",v["p16_sha"],"C3_P1_SHA=",v["p1_sha"])
 print("C3_QUANTIZED_COORDINATES=",len(changed),"C3_CHANGED_COORDINATE_DETAIL=",changed)
 print("C3_FROZEN_TOP1=",v["frozen_top11_ids"][0],"C3_BATCH16_TOP1=",order16[0],"C3_BATCH1_TOP1=",order1[0])
 print("C3_Q29_PAIR_GAPS=",v["score_gap_XPB018_minus_XPB027"])
 print("C3_BATCH_CHANGE_SCORE_EFFECT_ON_027=",delta.get("XPB027",0.0))
 print("STATUS=C3_CAUSAL_BATCH_INTERVENTION_RECORDED",flush=True)
if __name__=="__main__":main()
