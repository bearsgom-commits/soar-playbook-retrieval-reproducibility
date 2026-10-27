#!/usr/bin/env python3
"""C3-8B: corrected MPS B0 frozen ranking replication, 30 queries x 7 eps x 3 seeds."""
import sys,json,platform,time
from pathlib import Path
import numpy as np,torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference
from c3_mps_encoder_patch_trial import install
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
EPS=(0,2,4,8,16,32,64);SEEDS=(7,13,42)
def main():
 inp,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,_,_,_=prepare_inputs(inp)
 if not torch.backends.mps.is_available():raise RuntimeError("MPS_UNAVAILABLE")
 ids=plan["query_ids"];pids=plan["B0_anchor_ids"]
 assert len(ids)==30 and len(pids)==50
 reference=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="mps")
 patched=install(model,"all_linear");assert len(patched)==73
 tic=time.monotonic()
 query=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False).astype(np.float32)
 print("C3_8B_ENCODE=queries",len(query),"seconds",round(time.monotonic()-tic,2),flush=True)
 anchor=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False).astype(np.float32)
 print("C3_8B_ENCODE=anchors",len(anchor),"seconds",round(time.monotonic()-tic,2),flush=True)
 rows=[]; mismatches=[]
 for eps in EPS:
  for seed in SEEDS:
   qg=apply_guard_repr(query,eps,seed);pg=apply_guard_repr(anchor,eps,seed)
   rankings=dict(rank_top11(qg@pg.T,ids,pids))
   for qid in ids:
    actual=[p for p,s in rankings[qid][:10]]
    frozen=[x["electronics_id"] for x in reference[(eps,seed,qid)]["top_scored"][:10]]
    row={"epsilon":eps,"seed":seed,"query_id":qid,"top10_exact":actual==frozen,
         "top1_exact":actual[0]==frozen[0],"mps_top10":actual,"frozen_top10":frozen}
    rows.append(row)
    if not row["top10_exact"]:mismatches.append(row)
  print("C3_8B_EPS=",eps,"top10_exact",sum(r["top10_exact"] for r in rows if r["epsilon"]==eps),"/90",flush=True)
 summary={"track":"B0_anchor","n_queries":30,"n_playbooks":50,"epsilons":list(EPS),"seeds":list(SEEDS),
          "model_revision":MODEL_REV,"torch":torch.__version__,"platform":platform.platform(),
          "patched_linear_modules":len(patched),"total":len(rows),
          "top10_exact":sum(r["top10_exact"] for r in rows),
          "top1_exact":sum(r["top1_exact"] for r in rows),
          "mismatch_count":len(mismatches),"mismatches":mismatches,
          "elapsed_s":time.monotonic()-tic,
          "pass_gate":len(rows)==630 and not mismatches,
          "scope_boundary":"B0_anchor 630/2520 conditions only, source frozen original immutable"}
 (out/"c3_8b_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 with (out/"c3_8b_all_conditions.jsonl").open("w") as f:
  for r in rows:f.write(json.dumps(r)+"\n")
 print("C3_8B_TOTAL=",summary["total"],"TOP10_EXACT=",summary["top10_exact"],"TOP1_EXACT=",summary["top1_exact"],flush=True)
 print("C3_8B_Q29_EPS32_SEED7=",next(r for r in rows if r["query_id"]=="Q29" and r["epsilon"]==32 and r["seed"]==7),flush=True)
 print("C3_8B_GATE=","PASS" if summary["pass_gate"] else "FAIL",flush=True)
 print("STATUS=C3_8B_B0_FULL_COVERAGE_COMPLETE",flush=True)
if __name__=="__main__":main()
