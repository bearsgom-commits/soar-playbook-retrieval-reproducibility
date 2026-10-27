#!/usr/bin/env python3
"""R3-H: compare repeated raw/guard/score arrays and frozen rankings."""
import json
import sys
from pathlib import Path
import numpy as np

def main():
    root=Path(sys.argv[1])
    labels=["default_1","default_2","controlled_1","controlled_2"]
    reports={label:json.loads((root/label/"report.json").read_text(encoding="utf-8")) for label in labels}
    comparisons=[]
    for left,right in (("default_1","default_2"),("controlled_1","controlled_2"),
                       ("default_1","controlled_1"),("default_2","controlled_2")):
        pairs=[]
        for label in ("q","p","qg_7","pg_7","scores_7","qg_13","pg_13",
                      "scores_13","qg_42","pg_42","scores_42"):
            a=np.load(root/left/(label+".npy"))
            b=np.load(root/right/(label+".npy"))
            pairs.append({"array":label,"exact":bool(np.array_equal(a,b)),
                          "max_absolute_difference":float(np.max(np.abs(a.astype(np.float64)-b.astype(np.float64)))),
                          "number_different_elements":int(np.count_nonzero(a!=b))})
        comparisons.append({"left":left,"right":right,"arrays":pairs})
    outcome={
        "runs":{label:{
            "platform":reports[label]["platform"],
            "torch_threads":reports[label]["torch_num_threads"],
            "thread_env":reports[label]["thread_env"],
            "threadpool_info":reports[label]["threadpool_info"],
            "q_sha":reports[label]["q_sha"],
            "p_sha":reports[label]["p_sha"],
            "seeds":{seed:{
                "mismatch_count":v["mismatch_count"],
                "cases":[{"query_id":c["query_id"],"same_members":c["top10_members_equal"],
                          "same_top1":c["top1_equal"],
                          "observed_top10":c["observed_top10"]} for c in v["mismatches"]],
                "q_guard_sha":v["q_guard_sha"],"p_guard_sha":v["p_guard_sha"],
                "score_sha":v["score_sha"],"quantization_edge":v["projection_quantization_edge"],
            } for seed,v in reports[label]["seeds"].items()}
        } for label in labels},
        "comparisons":comparisons,
        "claim_boundary":"Read-only CPU numerical diagnostic; not an MPS source-compatible full replay."
    }
    (root/"r3h_aggregate.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2),encoding="utf-8")
    for comparison in comparisons:
        differences=[(x["array"],x["max_absolute_difference"],x["number_different_elements"])
                     for x in comparison["arrays"] if not x["exact"]]
        print(f"CROSS_RUN={comparison['left']}:{comparison['right']} NONIDENTICAL_ARRAYS={differences}",flush=True)
    for label in labels:
        print(f"RUN={label} MISMATCHES="+str({s:[c["query_id"] for c in v["mismatches"]]
               for s,v in reports[label]["seeds"].items()}),flush=True)
    print("STATUS=R3H_EVIDENCE_COLLECTED_NOT_SCIENTIFIC_PASS",flush=True)

if __name__=="__main__":
    main()
