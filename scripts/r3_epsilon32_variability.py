#!/usr/bin/env python3
"""R3-E: repeated independent CPU B0 replay. Writes diagnostic evidence only."""
from pathlib import Path
import sys,json,hashlib,platform
import numpy as np
import torch
import sentence_transformers
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs,MODEL_ID,MODEL_REV,EPS,SEEDS,rank_top11,load_reference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import apply_guard_repr
def sha(a):
 return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
 base,out,iteration=Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3])
 out.mkdir(parents=True,exist_ok=True)
 plan,_,_,_=prepare_inputs(base)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 assert model.max_seq_length==512 and model.default_prompt_name is None
 from huggingface_hub import hf_hub_download
 rev=getattr(model[0].auto_model.config,"_commit_hash",None)
 config=hf_hub_download(repo_id=MODEL_ID,filename="config.json",revision=MODEL_REV,local_files_only=True)
 snapshot_ok=("/snapshots/"+MODEL_REV+"/") in str(Path(config)).replace("\\\\","/")
 assert str(rev)==MODEL_REV or (rev is None and snapshot_ok), "MODEL_PINNED_SNAPSHOT_MISMATCH"
 q=model.encode(plan["arrays"]["B0_query"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 p=model.encode(plan["arrays"]["B0_anchor"],batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 assert q.shape==(30,768) and p.shape==(50,768) and q.dtype==np.float32 and p.dtype==np.float32
 ref=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 result={"iteration":iteration,"device":"cpu","platform":platform.platform(),"torch":torch.__version__,"sentence_transformers":sentence_transformers.__version__,"torch_num_threads":torch.get_num_threads(),"q_embedding_sha256":sha(q),"p_embedding_sha256":sha(p),"per_epsilon":{},"cases":[],"rankings":{},"epsilon32_score_sha256":{},"epsilon32_guard_embedding_sha256":{}}
 for eps in EPS:
  count10=count1=0
  for seed in SEEDS:
   qg=apply_guard_repr(q,eps,seed);pg=apply_guard_repr(p,eps,seed)
   matrix=qg@pg.T
   if eps==32:
    result["epsilon32_score_sha256"][str(seed)]=sha(matrix)
    result["epsilon32_guard_embedding_sha256"][str(seed)]={"q":sha(qg),"p":sha(pg)}
   ranks=rank_top11(matrix,plan["query_ids"],plan["B0_anchor_ids"])
   for qid,top in ranks:
    expected=ref[(eps,seed,qid)]["top_scored"]
    observed=[pid for pid,_ in top[:10]]
    frozen=[x["electronics_id"] for x in expected[:10]]
    key=f"{eps}/{seed}/{qid}"
    result["rankings"][key]=observed
    same10=observed==frozen
    count10+=same10
    count1+=observed[0]==frozen[0]
    if not same10:
     fs={x["electronics_id"]:float(x["score"]) for x in expected}
     rowindex=plan["query_ids"].index(qid)
     result["cases"].append({"epsilon":eps,"seed":seed,"query_id":qid,"top10_same_members":set(observed)==set(frozen),"top1_equal":observed[0]==frozen[0],"observed_top11":[{"id":pid,"score":float(val)} for pid,val in top],"frozen_top11":expected,"score_diff_for_common":{pid:float(matrix[rowindex,i])-fs[pid] for i,pid in enumerate(plan["B0_anchor_ids"]) if pid in fs and pid in observed},"observed_rank10_11_margin":float(top[9][1]-top[10][1])})
  result["per_epsilon"][str(eps)]={"top10_exact":count10,"top1_exact":count1,"total":90}
  print(f"ITERATION={iteration} EPS={eps} TOP10={count10}/90 TOP1={count1}/90",flush=True)
 result["top10_exact"]=sum(x["top10_exact"] for x in result["per_epsilon"].values())
 result["top1_exact"]=sum(x["top1_exact"] for x in result["per_epsilon"].values())
 (out/f"iteration_{iteration}.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 print(f"ITERATION={iteration} TOTAL_TOP10={result['top10_exact']}/630 TOP1={result['top1_exact']}/630 MISMATCHES={len(result['cases'])}",flush=True)
if __name__=="__main__":main()
