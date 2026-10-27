#!/usr/bin/env python3
"""C2 targeted E5 CPU-vs-MPS transformer-layer numerical attribution, Q01 only."""
from pathlib import Path
import json,sys,hashlib,platform
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def main():
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(base)
 assert plan["query_ids"][0]=="Q01"
 text=plan["arrays"]["C_query"][0]
 results={}
 for device in ("cpu","mps"):
  if device=="mps" and not torch.backends.mps.is_available():raise RuntimeError("MPS_UNAVAILABLE")
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
  assert model.max_seq_length==512 and model.default_prompt_name is None
  tokenizer=model[0].tokenizer
  tokens=tokenizer([text],padding=True,truncation=True,max_length=512,return_tensors="pt")
  input_ids=tokens["input_ids"].detach().cpu().numpy()
  attention=tokens["attention_mask"].detach().cpu().numpy()
  model[0].auto_model.eval()
  with torch.no_grad():
   inp={k:v.to(device) for k,v in tokens.items()}
   output=model[0].auto_model(**inp,output_hidden_states=True,return_dict=True)
   hidden=[x.detach().cpu().float().numpy() for x in output.hidden_states]
   mask=inp["attention_mask"].unsqueeze(-1).expand(output.last_hidden_state.size()).float()
   pooled=((output.last_hidden_state*mask).sum(dim=1)/mask.sum(dim=1).clamp(min=1e-9)).detach().cpu().numpy()
  official=model.encode([text],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
  results[device]={"tokens_sha":sha(input_ids),"attention_sha":sha(attention),
                  "hidden_sha":[sha(x) for x in hidden],"hidden":hidden,
                  "pooled":pooled,"official":official}
  print("DEVICE",device,"TOKEN_SHA",sha(input_ids),"LAYERS",len(hidden),
        "OFFICIAL_SHA",sha(official),flush=True)
 a,b=results["cpu"],results["mps"]
 if a["tokens_sha"]!=b["tokens_sha"]:raise RuntimeError("TOKEN_INPUT_MISMATCH")
 diffs=[]
 for i,(x,y) in enumerate(zip(a["hidden"],b["hidden"])):
  d=np.abs(x.astype(np.float64)-y.astype(np.float64))
  diffs.append({"layer":i,"sha_equal":sha(x)==sha(y),"max_abs":float(d.max()),
                "mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99))})
 def compare(x,y):
  d=np.abs(x.astype(np.float64)-y.astype(np.float64))
  return {"max_abs":float(d.max()),"mean_abs":float(d.mean()),"sha_equal":sha(x)==sha(y)}
 report={"model_revision":MODEL_REV,"platform":platform.platform(),"torch":torch.__version__,
         "query_id":"Q01","input_tokens_equal":True,"layer_differences":diffs,
         "first_divergent_layer":next((i for i,d in enumerate(diffs) if not d["sha_equal"]),None),
         "mean_pool_diff":compare(a["pooled"],b["pooled"]),
         "normalized_sentence_diff":compare(a["official"],b["official"]),
         "claim_boundary":"Q01 CPU/MPS intermediate numerical comparison; not proof of root hardware defect."}
 (out/"c2_layer_attribution.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("C2_FIRST_DIVERGENT_LAYER=",report["first_divergent_layer"],flush=True)
 print("C2_INPUT_EMBEDDING_DIFF=",diffs[0],flush=True)
 print("C2_FINAL_TRANSFORMER_DIFF=",diffs[-1],flush=True)
 print("C2_POOLED_DIFF=",report["mean_pool_diff"],flush=True)
 print("C2_SENTENCE_DIFF=",report["normalized_sentence_diff"],flush=True)
 print("STATUS=C2_LAYER_DIAGNOSTIC_COMPLETED",flush=True)
if __name__=="__main__":main()
