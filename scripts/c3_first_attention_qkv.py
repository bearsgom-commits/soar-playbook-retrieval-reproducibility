#!/usr/bin/env python3
"""C3-4 first-layer attention attribution: Q/K/V projections vs attention computation."""
import sys,json,platform,hashlib
from pathlib import Path
import numpy as np,torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def first_tensor(obj):
 if isinstance(obj,torch.Tensor):return obj
 if isinstance(obj,(tuple,list)):
  for v in obj:
   if isinstance(v,torch.Tensor):return v
 raise RuntimeError("NO_TENSOR_IN_HOOK")
def sample(model,text):
 m=model[0].auto_model; d={};hs=[]
 names=["embeddings","encoder.layer.0.attention.self.query",
        "encoder.layer.0.attention.self.key","encoder.layer.0.attention.self.value",
        "encoder.layer.0.attention.self","encoder.layer.0.attention.output"]
 modules=dict(m.named_modules())
 for name in names:
  if name not in modules:raise RuntimeError("MISSING_MODULE:"+name)
  def hook(mod,inputs,output,name=name):
   d[name]=first_tensor(output).detach().cpu().float().numpy().copy()
  hs.append(modules[name].register_forward_hook(hook))
 try:
  model.encode([text],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False)
 finally:
  for h in hs:h.remove()
 return d
def diff(x,y):
 d=np.abs(x.astype(np.float64)-y.astype(np.float64))
 return {"max_abs":float(d.max()),"mean_abs":float(d.mean()),
         "p99_abs":float(np.quantile(d,.99))}
def main():
 src,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(src);q=plan["arrays"]["C_query"][0]
 assert plan["query_ids"][0]=="Q01"
 data={}
 for dev in ("cpu","mps"):
  if dev=="mps" and not torch.backends.mps.is_available():raise RuntimeError("MPS_NOT_AVAILABLE")
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=dev)
  data[dev]=sample(model,q)
  del model
 stages={name:diff(data["cpu"][name],data["mps"][name]) for name in data["cpu"]}
 for name,v in stages.items():print("C3_QKV_STAGE=",name,v,flush=True)
 projection_max=max(stages[n]["max_abs"] for n in stages if n.endswith((".query",".key",".value")))
 selfdiff=stages["encoder.layer.0.attention.self"]["max_abs"]
 report={"model_rev":MODEL_REV,"torch":torch.__version__,"platform":platform.platform(),
         "query_id":"Q01","stages":stages,"max_qkv_projection_diff":projection_max,
         "self_attention_output_max_diff":selfdiff,
         "qkv_near_equal_1e-4":projection_max<1e-4,
         "attention_output_large_1e-2":selfdiff>1e-2,
         "limitation":"QKV-output tracing alone does not isolate attention mask, softmax or value matmul."}
 (out/"c3_qkv_attribution.json").write_text(json.dumps(report,indent=2))
 print("C3_QKV_NEAR_EQUAL=",report["qkv_near_equal_1e-4"])
 print("C3_SELF_OUTPUT_LARGE=",report["attention_output_large_1e-2"])
 print("STATUS=C3_QKV_ATTRIBUTION_COMPLETED")
if __name__=="__main__":main()
