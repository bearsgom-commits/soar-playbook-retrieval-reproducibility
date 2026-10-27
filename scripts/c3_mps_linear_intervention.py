#!/usr/bin/env python3
"""C3-6 targeted MPS linear operator intervention: matrix vs per-row vs f64 reference."""
from pathlib import Path
import sys,json,platform
import numpy as np,torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def difference(a,b):
 d=np.abs(a.astype(np.float64)-b.astype(np.float64))
 return {"max_abs":float(d.max()),"mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99))}
def cpu(x):return x.detach().to("cpu").numpy().astype(np.float64)
def main():
 inp,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(inp);assert plan["query_ids"][0]=="Q01"
 m=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")[0].auto_model.eval()
 t=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")[0].tokenizer([plan["arrays"]["C_query"][0]],padding=True,truncation=True,max_length=512,return_tensors="pt")
 with torch.no_grad():
  x=m.embeddings(input_ids=t["input_ids"],token_type_ids=torch.zeros_like(t["input_ids"]))[0].contiguous()
 result={"platform":platform.platform(),"torch":torch.__version__,"query_id":"Q01","cases":{}}
 for name in ("query","key","value"):
  l=getattr(m.encoder.layer[0].attention.self,name)
  w=l.weight.detach().contiguous();b=l.bias.detach()
  with torch.no_grad():
   ref=F.linear(x.double(),w.double(),b.double())
   cpu32=F.linear(x,w,b)
   xm=x.to("mps");wm=w.to("mps");bm=b.to("mps")
   mat=F.linear(xm,wm,bm)
   row=torch.cat([F.linear(xm[i:i+1],wm,bm) for i in range(xm.shape[0])],0)
   # independent GEMV-like vector multiplication; permits dispatch comparison.
   vec=torch.stack([torch.mv(wm,xm[i])+bm for i in range(xm.shape[0])],0)
  variants={"cpu32":cpu32,"mps_matrix":mat,"mps_rowwise":row,"mps_matvec":vec}
  comparisons={k:difference(cpu(v),cpu(ref)) for k,v in variants.items()}
  comparisons["mps_matrix_vs_mps_rowwise"]=difference(cpu(mat),cpu(row))
  comparisons["mps_matrix_vs_mps_matvec"]=difference(cpu(mat),cpu(vec))
  result["cases"][name]=comparisons
  print("C3_LINEAR_INTERVENTION=",name,json.dumps(comparisons),flush=True)
 best={k:min((v["max_abs"],name) for name,v in result["cases"][k].items() if name.startswith("mps_") and "_vs_" not in name) for k in result["cases"]}
 result["best_mps_method_by_operator"]=best
 result["criterion"]="A candidate method is useful only when its error vs CPU f64 drops substantially AND full E5 embedding and frozen ranks later recover."
 (out/"c3_linear_dispatch.json").write_text(json.dumps(result,indent=2))
 print("C3_BEST_MPS_METHODS=",best)
 print("STATUS=C3_LINEAR_INTERVENTION_COMPLETE",flush=True)
if __name__=="__main__":main()
