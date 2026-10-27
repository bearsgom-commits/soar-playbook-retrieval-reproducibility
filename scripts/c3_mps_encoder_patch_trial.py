#!/usr/bin/env python3
"""C3-7 isolated MPS linear correction trial, Q01 only, no source or frozen modifications."""
import sys,json,platform,types
from pathlib import Path
import numpy as np,torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def diff(a,b):
 d=np.abs(a.astype(np.float64)-b.astype(np.float64))
 return {"max_abs":float(d.max()),"mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99)),
         "cosine":float(np.dot(a,b))}
def infer(model,text):
 return model.encode([text],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False)[0].astype(np.float32)
def install(model,mode):
 replaced=[]
 for name,module in model[0].auto_model.named_modules():
  if not isinstance(module,nn.Linear):continue
  if mode=="first_qkv" and name not in ("encoder.layer.0.attention.self.query","encoder.layer.0.attention.self.key","encoder.layer.0.attention.self.value"):continue
  def forward(self,x):
   shape=x.shape
   inp=x.reshape(-1,shape[-1])
   # GEMV path on MPS: independently calculate every token's projection, preserving float32 and weights
   res=torch.stack([torch.mv(self.weight,row) for row in inp],dim=0)
   if self.bias is not None:res=res+self.bias
   return res.reshape(*shape[:-1],self.out_features)
  module.forward=types.MethodType(forward,module)
  replaced.append(name)
 return replaced
def main():
 source,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(source)
 assert plan["query_ids"][0]=="Q01"
 text=plan["arrays"]["C_query"][0]
 if not torch.backends.mps.is_available():raise RuntimeError("MPS_UNAVAILABLE")
 data={}
 for variant in ("cpu_default","mps_default","mps_first_qkv_mv","mps_all_linear_mv"):
  device="cpu" if variant.startswith("cpu") else "mps"
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
  changed=[]
  if variant=="mps_first_qkv_mv":changed=install(model,"first_qkv")
  elif variant=="mps_all_linear_mv":changed=install(model,"all_linear")
  vector=infer(model,text)
  data[variant]={"vector":vector,"modified_modules":changed}
  print("C3_PATCH_VARIANT=",variant,"MODIFIED_MODULES=",len(changed),"FIRST8=",vector[:8].tolist(),flush=True)
  del model
 ref=data["cpu_default"]["vector"]
 result={"model_revision":MODEL_REV,"torch":torch.__version__,"platform":platform.platform(),"query_id":"Q01",
         "variants":{name:{"changed_module_count":len(info["modified_modules"]),
                            "difference_vs_cpu":diff(ref,info["vector"])} for name,info in data.items()},
         "claim_boundary":"Single Q01 result. An encoder-level mitigation still requires all-tracks frozen-ranking verification."}
 result["initial_max_abs"]=result["variants"]["mps_default"]["difference_vs_cpu"]["max_abs"]
 result["patched_max_abs"]=result["variants"]["mps_all_linear_mv"]["difference_vs_cpu"]["max_abs"]
 result["improvement_ratio"]=result["initial_max_abs"]/max(result["patched_max_abs"],1e-30)
 (out/"c3_mps_encoder_patch_trial.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
 for k,v in result["variants"].items():print("C3_PATCH_RESULT=",k,json.dumps(v),flush=True)
 print("C3_PATCH_IMPROVEMENT_RATIO=",result["improvement_ratio"])
 print("C3_PATCH_STRICT_1E-5=",result["patched_max_abs"]<=1e-5)
 print("STATUS=C3_ENCODER_PATCH_TRIAL_FINISHED",flush=True)
if __name__=="__main__":main()
