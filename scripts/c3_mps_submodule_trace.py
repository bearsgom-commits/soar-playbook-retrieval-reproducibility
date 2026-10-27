#!/usr/bin/env python3
"""C3-3: compare frozen CPU/MPS XLM-R submodule outputs to locate first large drift."""
import sys,json,platform,re,hashlib
from pathlib import Path
import numpy as np,torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def fingerprint(model):
 h=hashlib.sha256()
 for k,p in model.state_dict().items():
  h.update(k.encode());h.update(p.detach().cpu().contiguous().numpy().tobytes())
 return h.hexdigest()
def tensor(z):
 if isinstance(z,torch.Tensor):return z
 if isinstance(z,(tuple,list)):
  for v in z:
   if isinstance(v,torch.Tensor):return v
 return None
def trace(model,text):
 core=model[0].auto_model;outputs={};handles=[]
 regex=re.compile(r"^(embeddings|encoder\.layer\.\d+\.(attention\.self|attention\.output|intermediate|output))$")
 for name,module in core.named_modules():
  if not regex.fullmatch(name):continue
  def hook(mod,inp,out,name=name):
   v=tensor(out)
   if v is not None:
    outputs[name]=v.detach().float().cpu().numpy().copy()
  handles.append(module.register_forward_hook(hook))
 try:
  vec=model.encode([text],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False)[0]
 finally:
  for h in handles:h.remove()
 return outputs,vec
def main():
 src,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(src)
 assert plan["query_ids"][0]=="Q01"
 q=plan["arrays"]["C_query"][0];data={};info={}
 for device in ["cpu","mps"]:
  if device=="mps" and not torch.backends.mps.is_available():raise RuntimeError("MPS_NOT_AVAILABLE")
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
  weight=fingerprint(model[0].auto_model)
  outputs,v=trace(model,q)
  data[device]=outputs;info[device]={"weight_sha":weight,"stage_count":len(outputs),"sentence_first8":v[:8].tolist()}
  print("DEVICE",device,"WEIGHT_SHA",weight,"STAGES",len(outputs),flush=True)
  del model
 if info["cpu"]["weight_sha"]!=info["mps"]["weight_sha"]:raise RuntimeError("WEIGHTS_NOT_IDENTICAL")
 if set(data["cpu"])!=set(data["mps"]) or len(data["cpu"])<30:raise RuntimeError("STAGE_COVERAGE_FAILURE "+str(len(data["cpu"])))
 stages=[]
 for k in data["cpu"]:
  a,b=data["cpu"][k],data["mps"][k]
  if a.shape!=b.shape:raise RuntimeError("STAGE_SHAPE_MISMATCH "+k)
  d=np.abs(a.astype(np.float64)-b.astype(np.float64))
  stages.append({"stage":k,"max_abs":float(d.max()),"mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99))})
 result={"model_revision":MODEL_REV,"platform":platform.platform(),"torch":torch.__version__,
  "query_id":"Q01","weights_identical":True,"metadata":info,"stages":stages,
  "first_gt_1e-3":next((s for s in stages if s["max_abs"]>1e-3),None),
  "first_gt_1e-2":next((s for s in stages if s["max_abs"]>1e-2),None),
  "conclusion_scope":"Submodule numerical divergence localisation, not yet a corrected backend."}
 (out/"c3_submodule_trace.json").write_text(json.dumps(result,indent=2))
 print("C3_STAGE_COUNT=",len(stages),"C3_FIRST_GT_1E-3=",result["first_gt_1e-3"],flush=True)
 print("C3_FIRST_GT_1E-2=",result["first_gt_1e-2"],flush=True)
 for s in stages:
  if s["stage"].startswith(("embeddings","encoder.layer.0.","encoder.layer.1.")):
   print("C3_EARLY_STAGE=",s,flush=True)
 print("STATUS=C3_SUBMODULE_TRACE_COMPLETE",flush=True)
if __name__=="__main__":main()
