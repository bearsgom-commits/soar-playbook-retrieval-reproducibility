#!/usr/bin/env python3
"""C3-5 same-input same-weight QKV operator intervention; frozen sources read only."""
import sys,json,platform,hashlib
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def cpuarr(x):return x.detach().to("cpu").float().numpy()
def delta(a,b):
 d=np.abs(a.astype(np.float64)-b.astype(np.float64))
 return {"max_abs":float(d.max()),"mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99))}
def main():
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(base)
 assert plan["query_ids"][0]=="Q01"
 text=plan["arrays"]["C_query"][0]
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 core=model[0].auto_model.eval()
 token=model[0].tokenizer([text],padding=True,truncation=True,max_length=model.max_seq_length,return_tensors="pt")
 with torch.no_grad():
  x=core.embeddings(input_ids=token["input_ids"],token_type_ids=torch.zeros_like(token["input_ids"]))
 layer=core.encoder.layer[0].attention.self
 report={"environment":{"platform":platform.platform(),"torch":torch.__version__},
  "model_revision":MODEL_REV,"query_id":"Q01","embedding_shape":list(x.shape),
  "tests":{},"interpretation_boundary":"Same captured CPU input and immutable CPU weights on CPU/MPS. This tests linear operator independently of model execution."}
 for name in ("query","key","value"):
  linear=getattr(layer,name)
  w=linear.weight.detach().clone().contiguous()
  b=linear.bias.detach().clone().contiguous() if linear.bias is not None else None
  with torch.no_grad():
   c=F.linear(x,w,b)
   m=F.linear(x.to("mps"),w.to("mps"),b.to("mps") if b is not None else None)
   m32=cpuarr(m)
   c32=cpuarr(c)
   # One-hot token feed establishes whether the same operator diverges for specific positions.
   per_token=np.max(np.abs(c32.astype(np.float64)-m32.astype(np.float64)),axis=2)[0]
   worst=int(np.argmax(per_token))
   # Compare model module output on CPU with the standalone operation (sanity check).
   cmodule=cpuarr(linear(x))
  res={"cpu_vs_mps_same_input":delta(c32,m32),
       "cpu_module_vs_functional":delta(c32,cmodule),
       "worst_token_index":worst,"worst_token_max_abs":float(per_token[worst]),
       "tokens_gt_1e-3":int(np.sum(per_token>1e-3)),
       "input_norm":float(torch.linalg.vector_norm(x)),
       "weight_dtype":str(w.dtype),"input_dtype":str(x.dtype)}
  report["tests"][name]=res
  print("C3_SAME_INPUT_QKV=",name,json.dumps(res),flush=True)
 report["any_linear_max_gt_1e-3"]=any(v["cpu_vs_mps_same_input"]["max_abs"]>1e-3 for v in report["tests"].values())
 (out/"c3_same_input_qkv.json").write_text(json.dumps(report,indent=2))
 print("C3_SAME_INPUT_LINEAR_DIVERGENCE=",report["any_linear_max_gt_1e-3"])
 print("STATUS=C3_SAME_INPUT_OPERATOR_DIAGNOSTIC_COMPLETED",flush=True)
if __name__=="__main__":main()
