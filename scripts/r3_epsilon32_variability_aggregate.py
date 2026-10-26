#!/usr/bin/env python3
"""Compare three independent R3-E executions, no source modification."""
import sys,json
from pathlib import Path
p=Path(sys.argv[1]);rows=[json.loads((p/f"iteration_{i}.json").read_text()) for i in (1,2,3)]
keys=sorted(rows[0]["rankings"])
variation=[{"condition":key,"top10":{str(r["iteration"]):r["rankings"][key] for r in rows}} for key in keys if len({tuple(r["rankings"][key]) for r in rows})>1]
out={"iterations":3,"totals":[{"iteration":r["iteration"],"top10_exact":r["top10_exact"],"top1_exact":r["top1_exact"],"mismatches":[{"epsilon":c["epsilon"],"seed":c["seed"],"query_id":c["query_id"],"top10_same_members":c["top10_same_members"],"top1_equal":c["top1_equal"]} for c in r["cases"]]} for r in rows],"q_embedding_shas":[r["q_embedding_sha256"] for r in rows],"p_embedding_shas":[r["p_embedding_sha256"] for r in rows],"eps32_score_shas":[r["epsilon32_score_sha256"] for r in rows],"eps32_guard_embedding_shas":[r["epsilon32_guard_embedding_sha256"] for r in rows],"rank_variation_count":len(variation),"rank_variation":variation,"diagnosis":"Repeated CPU cross-run comparison; this is not an MPS source-compatible reproduction pass."}
(p/"r3_e_variability_summary.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("R3E_TOP10_COUNTS=",[r["top10_exact"] for r in rows],flush=True)
print("R3E_TOP1_COUNTS=",[r["top1_exact"] for r in rows],flush=True)
print("R3E_Q_EMBEDDING_HASH_STABLE=",len(set(out["q_embedding_shas"]))==1,flush=True)
print("R3E_P_EMBEDDING_HASH_STABLE=",len(set(out["p_embedding_shas"]))==1,flush=True)
print("R3E_RANK_VARIATION_COUNT=",len(variation),flush=True)
print("STATUS=R3E_EVIDENCE_COLLECTED",flush=True)
