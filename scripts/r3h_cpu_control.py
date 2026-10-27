#!/usr/bin/env python3
"""R3-H: isolated CPU thread-control probe; only writes new diagnostic evidence."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import sentence_transformers
from sentence_transformers import SentenceTransformer
from threadpoolctl import threadpool_info

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import (
    MODEL_ID, MODEL_REV, SEEDS, prepare_inputs, rank_top11, load_reference
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from guard_repr import apply_guard_repr, l2_normalize, make_projection_matrix

def sha(arr):
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()

def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: worker.py INPUT_DIR OUTPUT_ROOT default|controlled ITERATION")
    base, root, mode, iteration = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
    if mode not in {"default", "controlled"} or iteration not in {1, 2}:
        raise ValueError("INVALID_PROBE_ARGUMENTS")
    if mode == "controlled":
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
    out = root / f"{mode}_{iteration}"
    out.mkdir(parents=True, exist_ok=False)
    plan, _, _, _ = prepare_inputs(base)
    model = SentenceTransformer(MODEL_ID, revision=MODEL_REV, device="cpu")
    if model.max_seq_length != 512 or model.default_prompt_name is not None:
        raise ValueError("MODEL_SETTINGS_DRIFT")
    q = model.encode(plan["arrays"]["B0_query"], batch_size=16, convert_to_numpy=True,
                     normalize_embeddings=True, show_progress_bar=False, prompt="")
    p = model.encode(plan["arrays"]["B0_anchor"], batch_size=16, convert_to_numpy=True,
                     normalize_embeddings=True, show_progress_bar=False, prompt="")
    if q.shape != (30, 768) or p.shape != (50, 768) or q.dtype != np.float32 or p.dtype != np.float32:
        raise ValueError("EMBEDDING_CONTRACT_DRIFT")
    np.save(out / "q.npy", q)
    np.save(out / "p.npy", p)
    ref_path = Path(__file__).resolve().parents[1] / "results/electronics/ranking_propagation/v1/source_rankings/B0_anchor_GUARD.jsonl"
    frozen = load_reference(ref_path)
    report = {
        "mode": mode, "iteration": iteration, "device": "cpu",
        "model_id": MODEL_ID, "model_revision": MODEL_REV,
        "platform": platform.platform(), "machine": platform.machine(),
        "torch_version": torch.__version__, "numpy_version": np.__version__,
        "sentence_transformers_version": sentence_transformers.__version__,
        "torch_num_threads": torch.get_num_threads(),
        "threadpool_info": threadpool_info(),
        "thread_env": {k: os.getenv(k) for k in
                       ("VECLIB_MAXIMUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS",
                        "OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")},
        "q_sha": sha(q), "p_sha": sha(p), "seeds": {},
    }
    for seed in SEEDS:
        qg = apply_guard_repr(q, 32, seed)
        pg = apply_guard_repr(p, 32, seed)
        scores = qg @ pg.T
        np.save(out / f"qg_{seed}.npy", qg)
        np.save(out / f"pg_{seed}.npy", pg)
        np.save(out / f"scores_{seed}.npy", scores)
        rankings = rank_top11(scores, plan["query_ids"], plan["B0_anchor_ids"])
        mismatches = []
        for qi, (qid, top) in enumerate(rankings):
            baseline = frozen[(32, seed, qid)]["top_scored"]
            observed_ids = [identifier for identifier, _ in top[:10]]
            frozen_ids = [item["electronics_id"] for item in baseline[:10]]
            if observed_ids == frozen_ids:
                continue
            mismatch = {
                "query_id": qid,
                "observed_top10": observed_ids,
                "frozen_top10": frozen_ids,
                "top10_members_equal": set(observed_ids) == set(frozen_ids),
                "top1_equal": observed_ids[0] == frozen_ids[0],
                "observed_top11": [
                    {"id":identifier,"score":float(value)} for identifier,value in top
                ],
                "frozen_top11": baseline,
                "observed_10_11_margin": float(top[9][1] - top[10][1]),
                "observed_top1_2_margin": float(top[0][1] - top[1][1]),
            }
            mismatches.append(mismatch)
        W = make_projection_matrix(768, 320, seed)
        projected = np.concatenate((l2_normalize(q) @ W, l2_normalize(p) @ W), axis=0)
        scaled = (np.clip(projected,-1,1) + 1) * (1023/2)
        fractional = scaled - np.floor(scaled)
        edge_dist = np.abs(fractional - 0.5)
        report["seeds"][str(seed)] = {
            "q_guard_sha": sha(qg), "p_guard_sha": sha(pg),
            "score_sha": sha(scores),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "projection_quantization_edge": {
                "min_distance_in_quantization_levels": float(edge_dist.min()),
                "count_within_1e-4": int((edge_dist < 1e-4).sum()),
                "count_within_1e-3": int((edge_dist < 1e-3).sum()),
            }
        }
        print(f"MODE={mode} ITERATION={iteration} SEED={seed} "
              f"Q_SHA={sha(q)} P_SHA={sha(p)} QG_SHA={sha(qg)} PG_SHA={sha(pg)} "
              f"SCORE_SHA={sha(scores)} MISMATCHES={len(mismatches)} "
              f"CASES={[c['query_id'] for c in mismatches]}", flush=True)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STATUS=R3H_{mode.upper()}_{iteration}_EVIDENCE_SAVED", flush=True)

if __name__ == "__main__":
    main()
