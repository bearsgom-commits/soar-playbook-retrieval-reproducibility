#!/usr/bin/env python3
"""C3-8 gated four-track reproducibility smoke test; immutable frozen inputs and rankings."""
import sys,json,platform,hashlib
from pathlib import Path
import numpy as np,torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference
from c3_mps_encoder_patch_trial import install
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def encode(model,x):
 return model.encode(x,batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False).astype(np.float32)
def main():
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,playbooks,queries,anchors=prepare_inputs(base)
 if not torch.backends.mps.is_available():raise RuntimeError("MPS_NOT_AVAILABLE")
 # Begin with a deliberately bounded independent anchor track to avoid expensive full-corpus GEMV.
 qids=plan["query_ids"];qselect=["Q03","Q12","Q29"]
 idx=[qids.index(q) for q in qselect]
 pids=plan["B0_anchor_ids"];ref=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 arrays={}
 for device in ("cpu","mps"):
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
  patched=install(model,"all_linear") if device=="mps" else []
  q=encode(model,[plan["arrays"]["B0_query"][i] for i in idx])
  p=encode(model,plan["arrays"]["B0_anchor"])
  arrays[device]=(q,p)
  print("C3_8_ENCODED=",device,"queries",len(q),"anchors",len(p),"patched_modules",len(patched),flush=True)
  del model
 output={"scope":"B0 anchor only; 3 previously mismatching queries at epsilon32 seed7; pre-gate, not full reproduction",
         "platform":platform.platform(),"torch":torch.__version__,"model_revision":MODEL_REV,
         "conditions":[]}
 cq,cp=arrays["cpu"];mq,mp=arrays["mps"]
 output["cpu_mps_max_q_abs"]=float(np.abs(cq-mq).max())
 output["cpu_mps_max_p_abs"]=float(np.abs(cp-mp).max())
 for eps,seed in ((32,7),(16,42),(64,7)):
  results={}
  for device,(q,p) in arrays.items():
   qg=apply_guard_repr(q,eps,seed);pg=apply_guard_repr(p,eps,seed)
   ranked=dict(rank_top11(qg@pg.T,qselect,pids))
   results[device]={qid:[pid for pid,score in ranked[qid][:10]] for qid in qselect}
  for qid in qselect:
   frozen=[r["electronics_id"] for r in ref[(eps,seed,qid)]["top_scored"][:10]]
   row={"epsilon":eps,"seed":seed,"query_id":qid,
        "cpu_vs_mps_top10":results["cpu"][qid]==results["mps"][qid],
        "cpu_vs_frozen_top10":results["cpu"][qid]==frozen,
        "mps_vs_frozen_top10":results["mps"][qid]==frozen,
        "cpu_top1":results["cpu"][qid][0],"mps_top1":results["mps"][qid][0],"frozen_top1":frozen[0],
        "cpu_top10":results["cpu"][qid],"mps_top10":results["mps"][qid],"frozen_top10":frozen}
   output["conditions"].append(row)
   print("C3_8_RANK=",qid,eps,seed,"CPU_EQ_MPS",row["cpu_vs_mps_top10"],
         "CPU_EQ_FROZEN",row["cpu_vs_frozen_top10"],
         "MPS_EQ_FROZEN",row["mps_vs_frozen_top10"],"TOP1",row["cpu_top1"],row["mps_top1"],row["frozen_top1"],flush=True)
 output["cpu_mps_exact_count"]=sum(x["cpu_vs_mps_top10"] for x in output["conditions"])
 output["patched_mps_frozen_exact_count"]=sum(x["mps_vs_frozen_top10"] for x in output["conditions"])
 output["cpu_frozen_exact_count"]=sum(x["cpu_vs_frozen_top10"] for x in output["conditions"])
 output["total"]=len(output["conditions"])
 output["full_run_gate"]="PROCEED_TO_FULL_ONLY_IF_CPU_MPS_EXACT_AND_SOURCE_COMPATIBILITY_CAVEATS_UNDERSTOOD" if output["cpu_mps_exact_count"]==output["total"] else "STOP_INVESTIGATE_GUARD_OR_EMBEDDING"
 (out/"c3_8_smoke.json").write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
 print("C3_8_COUNTS=",json.dumps({k:output[k] for k in ("cpu_mps_exact_count","cpu_frozen_exact_count","patched_mps_frozen_exact_count","total","full_run_gate")}),flush=True)
 print("STATUS=C3_8_SMOKE_COMPLETE",flush=True)
if __name__=="__main__":main()
