#!/usr/bin/env python3
"""C3-8C: one corrected-MPS encoding, 3 remaining tracks x 630 frozen conditions."""
import sys,json,time,platform,hashlib
from pathlib import Path
import numpy as np,torch
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,rank_top11,load_reference,EPS,SEEDS
from c3_mps_encoder_patch_trial import install
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def main():
 inp,out=Path(sys.argv[1]),Path(sys.argv[2])
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 plan,playbooks,_,_=prepare_inputs(inp)
 if not torch.backends.mps.is_available():raise RuntimeError("MPS_UNAVAILABLE")
 ids=plan["query_ids"];assert len(ids)==30 and len(playbooks)==1606
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="mps")
 patched=install(model,"all_linear");assert len(patched)==73
 start=time.monotonic()
 emb={}
 for key in ("C_query","C_broad"):
  texts=plan["arrays"][key]
  parts=[]
  for st in range(0,len(texts),16):
   chunk=model.encode(texts[st:st+16],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,prompt="",show_progress_bar=False).astype(np.float32)
   if chunk.shape!=(len(texts[st:st+16]),768) or not np.isfinite(chunk).all():raise ValueError("EMBEDDING_CONTRACT_FAIL "+key)
   parts.append(chunk)
   if st==0 or (st//16+1)%10==0 or st+16>=len(texts):
    print("C3_8C_ENCODING=",key,min(st+16,len(texts)),"/",len(texts),"elapsed_s",round(time.monotonic()-start,1),flush=True)
  emb[key]=np.concatenate(parts,axis=0)
 del model
 all_ids=[r["electronics_id"] for r in playbooks]
 primary=[i for i,r in enumerate(playbooks) if r["track_c_stratum"]=="PRIMARY_MACHINE_SELECTED"]
 assert len(primary)==830
 tracks={
  "B1_anchor":(emb["C_query"],emb["C_broad"][plan["B1_broad_indices"]],plan["B0_anchor_ids"]),
  "C_primary":(emb["C_query"],emb["C_broad"][primary],[all_ids[i] for i in primary]),
  "C_broad":(emb["C_query"],emb["C_broad"],all_ids)}
 summary={"scope":"three remaining tracks (1890 conditions); corrected MPS all-linear GEMV","torch":torch.__version__,
          "platform":platform.platform(),"model_revision":MODEL_REV,"patched_linear_modules":len(patched),
          "frozen_inputs_validated":True,"tracks":{}}
 all_rows=[]
 root=Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings"
 for track,(q,p,pids) in tracks.items():
  ref=load_reference(root/(track+"_GUARD.jsonl"))
  match10=match1=0;bad=[]
  for eps in EPS:
   for seed in SEEDS:
    ranked=dict(rank_top11(apply_guard_repr(q,eps,seed)@apply_guard_repr(p,eps,seed).T,ids,pids))
    for qid in ids:
     actual=[n for n,v in ranked[qid][:10]]
     frozen=[r["electronics_id"] for r in ref[(eps,seed,qid)]["top_scored"][:10]]
     eq10=(actual==frozen);eq1=(actual[0]==frozen[0])
     match10+=eq10;match1+=eq1
     row={"track":track,"epsilon":eps,"seed":seed,"query_id":qid,"exact_top10":eq10,"exact_top1":eq1}
     all_rows.append(row)
     if not eq10:bad.append({**row,"actual_top10":actual,"frozen_top10":frozen})
   print("C3_8C_TRACK_EPS=",track,eps,"top10_exact",sum(r["exact_top10"] for r in all_rows if r["track"]==track and r["epsilon"]==eps),"/90",flush=True)
  summary["tracks"][track]={"total":630,"top10_exact":match10,"top1_exact":match1,"mismatch_count":len(bad),"mismatches":bad}
  print("C3_8C_TRACK=",track,"TOP10",match10,"/630 TOP1",match1,"/630",flush=True)
 summary["total"]=len(all_rows)
 summary["top10_exact"]=sum(r["exact_top10"] for r in all_rows)
 summary["top1_exact"]=sum(r["exact_top1"] for r in all_rows)
 summary["pass_gate"]=summary["total"]==1890 and summary["top10_exact"]==1890
 summary["elapsed_seconds"]=round(time.monotonic()-start,1)
 (out/"c3_8c_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
 with (out/"c3_8c_all_conditions.jsonl").open("w") as f:
  for row in all_rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
 print("C3_8C_TOTAL=",summary["total"],"TOP10_EXACT=",summary["top10_exact"],"TOP1_EXACT=",summary["top1_exact"],flush=True)
 print("C3_8C_GATE=","PASS" if summary["pass_gate"] else "FAIL",flush=True)
 print("STATUS=C3_8C_COMPLETED",flush=True)
if __name__=="__main__":main()
