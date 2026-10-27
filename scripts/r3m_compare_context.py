#!/usr/bin/env python3
"""Compare R3-H and R3-L under the same CI runner, CPU env and pinned dependencies."""
import json,sys
from pathlib import Path
h=json.loads((Path(sys.argv[1])/"controlled_1"/"report.json").read_text())
l=json.loads((Path(sys.argv[2])/"r3l_attribution.json").read_text())
print("R3M_H_THREADS=",h["torch_num_threads"],"R3M_L_THREADS=",l["environment"]["threads"],flush=True)
print("R3M_QUERY_EQUAL=",h["q_sha"]==l["q16_sha"],flush=True)
for name,v in l["anchors"].items():
 print("R3M_ANCHOR",name,"H_EQUAL",v["sha"]==h["p_sha"],"L_SHA",v["sha"],"H_SHA",h["p_sha"],flush=True)
print("R3M_H_ENV=",h["thread_env"],flush=True)
print("R3M_L_ENV=",l["environment"]["thread_env"],flush=True)
print("R3M_H_POOLS=",h["threadpool_info"],flush=True)
print("R3M_L_POOLS=",l["environment"]["threadpools"],flush=True)
report={"h_q_sha":h["q_sha"],"h_p_sha":h["p_sha"],"l_q_sha":l["q16_sha"],
 "l_anchor_shas":{k:v["sha"] for k,v in l["anchors"].items()},
 "q_exact_sha":h["q_sha"]==l["q16_sha"],
 "p_batch16_exact_sha":h["p_sha"]==l["anchors"]["batch16"]["sha"],
 "h_thread_env":h["thread_env"],"l_thread_env":l["environment"]["thread_env"],
 "h_threadpools":h["threadpool_info"],"l_threadpools":l["environment"]["threadpools"],
 "status":"EVIDENCE_COLLECTED_CAUSE_NOT_AUTOMATICALLY_PROVEN"}
Path(sys.argv[3]).mkdir(parents=True,exist_ok=True)
(Path(sys.argv[3])/"r3m_compare.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("STATUS=R3M_COLLECTED",flush=True)
