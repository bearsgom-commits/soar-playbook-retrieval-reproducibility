#!/usr/bin/env python3
"""R3-L controlled local CPU numerical attribution; no research source mutation."""
from pathlib import Path
import sys,json,hashlib,os,platform
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from threadpoolctl import threadpool_info
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs, MODEL_ID, MODEL_REV, SEEDS, rank_top11, load_reference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from guard_repr import l2_normalize,make_projection_matrix,uniform_quantize,apply_guard_repr

def sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def diff(a,b):
 d=np.abs(a.astype(np.float64)-b.astype(np.float64))
 return {"exact":bool(np.array_equal(a,b)),"different":int(np.count_nonzero(a!=b)),
         "max_abs":float(d.max()),"mean_abs":float(d.mean()),"p99_abs":float(np.quantile(d,.99))}
def stages(x,seed):
 w=make_projection_matrix(768,320,seed)
 norm=l2_normalize(x); proj=norm@w
 quant=uniform_quantize(proj,10); guard=l2_normalize(quant)
 return {"norm":norm,"projected":proj,"quantized":quant,"guard":guard}
def main():
 base,out=Path(sys.argv[1]),Path(sys.argv[2])
 out.mkdir(parents=True,exist_ok=False)
 torch.set_num_threads(1);torch.set_num_interop_threads(1)
 plan,_,_,_=prepare_inputs(base)
 model=SentenceTransformer(MODEL_ID,revision=MODEL_REV,device="cpu")
 assert model.max_seq_length==512 and model.default_prompt_name is None
 def encode(texts,batch):
  return model.encode(texts,batch_size=batch,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,prompt="")
 q16=encode(plan["arrays"]["B0_query"],16)
 p16=encode(plan["arrays"]["B0_anchor"],16)
 p1=encode(plan["arrays"]["B0_anchor"],1)
 p16_repeat=encode(plan["arrays"]["B0_anchor"],16)
 # Test order sensitivity by interleaving query and anchor.
 q16_repeat=encode(plan["arrays"]["B0_query"],16)
 p16_after_query=encode(plan["arrays"]["B0_anchor"],16)
 assert q16.shape==(30,768) and p16.shape==(50,768)
 frozen=load_reference(Path(__file__).resolve().parents[1]/"results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl")
 references={"r3f_q":"b11f760ef601335ce9fa26ad3df6566cc6998b962bc6979e16b5a955fc99a42c",
  "r3f_p":"49439bc86423efee041e19ba8b6ffbdca1e10d74db7ed55afecbf6a8786d0b8d",
  "r3h_controlled_p":"fbde0e490fb7aceb2e96d42151b3b8e68474914c6404468912660fbe827dbbe6",
  "r3h_default_p":"a68e36221c0ac2a0a1a8352294e02f147c58d194510451449bb19c1cf028bf07"}
 options={"batch16":p16,"batch1":p1,"batch16_repeat":p16_repeat,"batch16_after_query":p16_after_query}
 report={"environment":{"platform":platform.platform(),"torch":torch.__version__,"threads":torch.get_num_threads(),
       "thread_env":{k:os.getenv(k) for k in ["OMP_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"]},
       "threadpools":threadpool_info()},"q16_sha":sha(q16),"q16_repeat_sha":sha(q16_repeat),
       "anchors":{},"pairwise":[],"by_seed":{}}
 for name,p in options.items():
  report["anchors"][name]={"sha":sha(p),"matching_prior":[k for k,v in references.items() if sha(p)==v]}
 for left,right in [("batch16","batch1"),("batch16","batch16_repeat"),("batch16","batch16_after_query"),
                     ("batch1","batch16_after_query")]:
  report["pairwise"].append({"left":left,"right":right,**diff(options[left],options[right])})
 for seed in SEEDS:
  qs=stages(q16,seed)
  variants={}
  qg=qs["guard"]
  for name,p in options.items():
   s=stages(p,seed)
   scores=qg@s["guard"].T
   ranks=rank_top11(scores,plan["query_ids"],plan["B0_anchor_ids"])
   mismatch=[]
   for qid,top in ranks:
    expected=[x["electronics_id"] for x in frozen[(32,seed,qid)]["top_scored"][:10]]
    observed=[x[0] for x in top[:10]]
    if observed!=expected:
     mismatch.append({"qid":qid,"top1_equal":observed[0]==expected[0],"members_equal":set(observed)==set(expected)})
   variants[name]={"hashes":{k:sha(v) for k,v in s.items()},"scores_sha":sha(scores),"mismatches":mismatch}
  pairs=[]
  for other in ["batch1","batch16_repeat","batch16_after_query"]:
   left=stages(p16,seed);right=stages(options[other],seed)
   pairs.append({"against":other,"stage_differences":{k:diff(left[k],right[k]) for k in left},
       "changed_quantized_coordinates":int(np.count_nonzero(left["quantized"]!=right["quantized"]))})
  report["by_seed"][str(seed)]={"variants":variants,"stage_comparisons":pairs}
  print("SEED",seed,"MISMATCHES",{k:[c["qid"] for c in v["mismatches"]] for k,v in variants.items()},
        "CHANGED_QUANTIZED",{x["against"]:x["changed_quantized_coordinates"] for x in pairs},flush=True)
 print("ANCHOR_HASHES",{k:v["sha"] for k,v in report["anchors"].items()},flush=True)
 print("ANCHOR_DIFFS",report["pairwise"],flush=True)
 (out/"r3l_attribution.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
 print("STATUS=R3L_DIAGNOSTIC_COMPLETED_NO_REPRO_PASS_ASSERTED",flush=True)
if __name__=="__main__":main()
