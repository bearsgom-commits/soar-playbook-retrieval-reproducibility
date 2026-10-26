#!/usr/bin/env python3
"""Read-only R2 single-query CPU/MPS diagnostic using exact frozen input."""
from pathlib import Path
import sys,json,hashlib,platform
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV
def main():
 plan,_,_,_=prepare_inputs(Path(sys.argv[1]))
 out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
 q=plan["arrays"]["C_query"][0]
 assert plan["query_ids"][0]=="Q01"
 report={"model_revision":MODEL_REV,"platform":platform.platform(),"query_id":"Q01","input_sha256":hashlib.sha256(q.encode()).hexdigest(),"torch":torch.__version__,"results":{}}
 for device in ("cpu","mps"):
  if device=="mps" and not torch.backends.mps.is_available():raise RuntimeError("MPS_NOT_AVAILABLE")
  model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device=device)
  v=model.encode([q],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")[0].astype(np.float32)
  np.save(out/("q01_"+device+".npy"),v)
  report["results"][device]={"sha256":hashlib.sha256(v.tobytes()).hexdigest(),"first8":v[:8].tolist(),"norm":float(np.linalg.norm(v))}
  print("DEVICE",device,"SHA256",report["results"][device]["sha256"],"FIRST8",report["results"][device]["first8"],flush=True)
  del model
 a=np.load(out/"q01_cpu.npy");b=np.load(out/"q01_mps.npy")
 report["cpu_mps_max_abs_diff"]=float(np.max(np.abs(a-b)))
 report["cpu_mps_cosine"]=float(np.dot(a,b))
 (out/"r2_ci_probe.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("CPU_MPS_MAX_ABS_DIFF=",report["cpu_mps_max_abs_diff"],flush=True)
 print("STATUS=PASS_R2_CI_PROBE",flush=True)
if __name__=="__main__":main()
