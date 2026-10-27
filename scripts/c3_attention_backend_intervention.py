#!/usr/bin/env python3
"""C3-2: test an actual attention-backend intervention, not merely observe divergence."""
from pathlib import Path
import json,sys,platform
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def main():
 src,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(src);q=plan["arrays"]["C_query"][0]
 assert plan["query_ids"][0]=="Q01"
 vectors={};details={}
 for device in ("cpu","mps"):
  if device=="mps" and not torch.backends.mps.is_available():raise RuntimeError("MPS_NOT_AVAILABLE")
  for mode in ("default","eager"):
   model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
   impl_before=getattr(model[0].auto_model.config,"_attn_implementation",None)
   if mode=="eager":
    setter=getattr(model[0].auto_model,"set_attn_implementation",None)
    if setter is None:raise RuntimeError("SET_ATTN_IMPLEMENTATION_NOT_SUPPORTED")
    setter("eager")
    if getattr(model[0].auto_model.config,"_attn_implementation",None)!="eager":
     raise RuntimeError("EAGER_NOT_APPLIED")
   impl_after=getattr(model[0].auto_model.config,"_attn_implementation",None)
   v=model.encode([q],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False).astype(np.float32)[0]
   vectors[(device,mode)]=v
   details[f"{device}_{mode}"]={"implementation_before":impl_before,"implementation_after":impl_after,
                                "norm":float(np.linalg.norm(v))}
   print("C3_ATTN_MODE=",device,mode,"before",impl_before,"after",impl_after,flush=True)
   del model
 def diff(x,y):
  a,b=vectors[x],vectors[y]
  return {"max_abs":float(np.max(np.abs(a-b))),
          "mean_abs":float(np.mean(np.abs(a-b))),
          "cosine":float(np.dot(a,b))}
 results={
  "environment":{"platform":platform.platform(),"torch":torch.__version__},
  "model_revision":MODEL_REV,"query_id":"Q01","implementations":details,
  "cpu_default_vs_mps_default":diff(("cpu","default"),("mps","default")),
  "cpu_eager_vs_mps_eager":diff(("cpu","eager"),("mps","eager")),
  "cpu_default_vs_cpu_eager":diff(("cpu","default"),("cpu","eager")),
  "mps_default_vs_mps_eager":diff(("mps","default"),("mps","eager"))}
 (out/"c3_attention_backend_test.json").write_text(json.dumps(results,indent=2))
 print("C3_DEFAULT_CPU_MPS_DIFF=",results["cpu_default_vs_mps_default"])
 print("C3_EAGER_CPU_MPS_DIFF=",results["cpu_eager_vs_mps_eager"])
 improve=results["cpu_eager_vs_mps_eager"]["max_abs"]<results["cpu_default_vs_mps_default"]["max_abs"]
 print("C3_EAGER_REDUCED_ERROR=",improve)
 print("C3_EAGER_SOLVED_STRICT_1E-5=",results["cpu_eager_vs_mps_eager"]["max_abs"]<=1e-5)
 print("STATUS=C3_ATTENTION_INTERVENTION_OBSERVED_NOT_FULL_REPRODUCTION",flush=True)
if __name__=="__main__":main()
