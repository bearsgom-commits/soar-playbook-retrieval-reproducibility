#!/usr/bin/env python3
"""Opt-in scientific re-execution: frozen E5 encoder + original Guard transform.

Requires locally obtained *exact* JSONL inputs and a pinned SentenceTransformer
model. Never changes frozen source data or public output. It writes to a new
user-specified directory and compares observed vs frozen GUARD rank-11 records.

--verify-inputs validates all 4 files without downloading or running a model.
macOS MPS is source-compatible; CPU results are cross-backend diagnostics only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from electronics.encoder_runner import build_input_plan, read_jsonl
from guard_repr import apply_guard_repr, eps_to_repr_spec

EXPECTED = {
    "playbook_source_clean_inputs.jsonl": "bafbf21b08f70de1355ea5bb985c4e57421fd35d56deb77b639dc4e168c94d89",
    "query_source_clean_inputs.jsonl": "e72be8067f94bf72c69d6cb69e9cbd3e431a8153e1c5ade468283fa9040c453c",
    "anchor_50_clean_binding.jsonl": "c404fea3d583a61932c0ca5a0c33212575acd5215468e8490367991c789f237b",
    "token_lengths.jsonl": "9732e3ba440d42397e09a629d648f4c4e573bcc8ef2aac6a0fe63d3b3e31c14a",
}
MODEL_ID = "intfloat/multilingual-e5-base"
MODEL_REV = "d128750597153bb5987e10b1c3493a34e5a4502a"
EPS = (0, 2, 4, 8, 16, 32, 64)
SEEDS = (7, 13, 42)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare_inputs(base):
    for name, expected_hash in EXPECTED.items():
        actual = sha256_file(base / name)
        if actual != expected_hash:
            raise ValueError(f"FROZEN_INPUT_SHA_MISMATCH: {name}: {actual}")
    playbooks = read_jsonl(base / "playbook_source_clean_inputs.jsonl")
    queries = read_jsonl(base / "query_source_clean_inputs.jsonl")
    anchors = read_jsonl(base / "anchor_50_clean_binding.jsonl")
    lengths = read_jsonl(base / "token_lengths.jsonl")
    if len(lengths) != 1766:
        raise ValueError("TOKEN_RECORD_COUNT_CHANGED")
    plan = build_input_plan(playbooks, queries, anchors)
    if sum(row["track_c_stratum"] == "PRIMARY_MACHINE_SELECTED" for row in playbooks) != 830:
        raise ValueError("PRIMARY_CORPUS_SIZE_CHANGED")
    print("PASS: original JSONL input hashes, counts, and B0/B1 anchor text bindings")
    return plan, playbooks, queries, anchors


def rank_top11(matrix, query_ids, playbook_ids):
    import numpy as np
    if matrix.shape != (len(query_ids), len(playbook_ids)):
        raise ValueError("SCORE_MATRIX_SHAPE_DRIFT")
    outputs = []
    for qi, qid in enumerate(query_ids):
        scored = [
            (pid, float(matrix[qi, di]))
            for di, pid in enumerate(playbook_ids)
        ]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        outputs.append((qid, scored[:11]))
    return outputs


def load_reference(path):
    lookup = {}
    if not path.is_file():
        raise FileNotFoundError(f"Missing frozen GUARD rank reference: {path}")
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            key = (int(row["epsilon"]), int(row["seed"]), row["query_id"])
            if key in lookup:
                raise ValueError(f"DUPLICATE_FROZEN_CONDITION: {path}:{key}")
            lookup[key] = row
    if len(lookup) != 630:
        raise ValueError(f"UNEXPECTED_FROZEN_CONDITION_COUNT: {path}:{len(lookup)}")
    return lookup


def compare_guard(track, epsilon, seed, rankings, ref):
    exact_top10 = exact_top1 = 0
    max_score_diff = 0.0
    for qid, top in rankings:
        row = ref[(epsilon, seed, qid)]
        expected = row["top_scored"]
        observed_ids = [id for id, _ in top[:10]]
        expected_ids = [item["electronics_id"] for item in expected[:10]]
        exact_top10 += observed_ids == expected_ids
        exact_top1 += observed_ids[0] == expected_ids[0]
        expected_score_by_id = {
            item["electronics_id"]: float(item["score"]) for item in expected
        }
        for identifier, score in top:
            if identifier in expected_score_by_id:
                max_score_diff = max(max_score_diff, abs(score - expected_score_by_id[identifier]))
    return exact_top10, exact_top1, max_score_diff


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", required=True, type=Path, help="Directory holding the original four JSONL files")
    p.add_argument("--device", default="cpu", choices=["cpu", "mps"])
    p.add_argument("--out", default=None, type=Path)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--verify-inputs", action="store_true", help="No model download or experiment")
    args = p.parse_args()

    plan, playbooks, queries, anchors = prepare_inputs(args.inputs)
    if args.verify_inputs:
        print("INPUT_ONLY_AUDIT=PASS; SCIENTIFIC_EXPERIMENT_EXECUTED=NO")
        return
    if args.out is None:
        raise ValueError("--out must designate a new output directory")
    if args.out.exists():
        raise FileExistsError(f"Do not overwrite existing output: {args.out}")
    if args.batch_size < 1:
        raise ValueError("Invalid batch size")

    import numpy as np
    import sklearn
    import torch
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    
    if args.device == "mps" and not torch.backends.mps.is_available():
        raise EnvironmentError("MPS requested but unavailable")
    model = SentenceTransformer(MODEL_ID, revision=MODEL_REV, device=args.device)
    from huggingface_hub import hf_hub_download
    internal_rev = getattr(model[0].auto_model.config, "_commit_hash", None)
    config_path = hf_hub_download(repo_id=MODEL_ID, filename="config.json", revision=MODEL_REV, local_files_only=True)
    snapshot_valid = ("/snapshots/" + MODEL_REV + "/") in str(Path(config_path)).replace("\\\\", "/")
    if not (str(internal_rev) == MODEL_REV or (internal_rev is None and snapshot_valid)):
        raise EnvironmentError(f"MODEL_PINNED_SNAPSHOT_MISMATCH: observed={internal_rev}, path={config_path}")
    observed_rev = MODEL_REV
    revision_source = "config._commit_hash" if internal_rev is not None else "cached_exact_snapshot_path"
    if model.max_seq_length != 512:
        raise EnvironmentError(f"MAX_SEQ_LENGTH_MISMATCH: {model.max_seq_length}")
    if model.default_prompt_name is not None:
        raise EnvironmentError("UNEXPECTED_DEFAULT_PROMPT")

    emb = {}
    for name in ("C_query", "C_broad", "B0_query", "B0_anchor"):
        texts = plan["arrays"][name]
        arr = model.encode(
            texts,
            batch_size=args.batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
            prompt="",
        )
        if arr.dtype != np.float32 or arr.shape != (len(texts), 768):
            raise ValueError(f"ENCODER_CONTRACT_MISMATCH: {name}:{arr.shape}:{arr.dtype}")
        if not np.isfinite(arr).all():
            raise ValueError(f"NONFINITE_EMBEDDINGS: {name}")
        emb[name] = arr
        print(f"ENCODED {name} {len(texts)} x 768", flush=True)

    full_ids = [r["electronics_id"] for r in playbooks]
    prim_idx = [i for i, r in enumerate(playbooks) if r["track_c_stratum"] == "PRIMARY_MACHINE_SELECTED"]
    anchor_idx = plan["B1_broad_indices"]
    anchor_ids = plan["B0_anchor_ids"]
    query_ids = plan["query_ids"]
    # B1 and C-primary use exact *views* of C-broad embeddings,
    # not an independently re-encoded playbook corpus.
    tracks = {
        "B0_anchor": (emb["B0_query"], emb["B0_anchor"], anchor_ids),
        "B1_anchor": (emb["C_query"], emb["C_broad"][anchor_idx], anchor_ids),
        "C_primary": (emb["C_query"], emb["C_broad"][prim_idx], [full_ids[i] for i in prim_idx]),
        "C_broad": (emb["C_query"], emb["C_broad"], full_ids),
    }
    reference_root = ROOT / "results/electronics/ranking_propagation/v1/source_rankings"
    ref = {track:load_reference(reference_root / (track + "_GUARD.jsonl")) for track in tracks}
    args.out.mkdir(parents=True, exist_ok=False)
    report = {
        "scientific_execution": True,
        "source_compatible_backend": args.device == "mps",
        "device": args.device,
        "platform": platform.platform(),
        "python": sys.version,
        "torch": torch.__version__,
        "numpy": np.__version__,
        "sentence_transformers": sentence_transformers.__version__,
        "sklearn": sklearn.__version__,
        "model_revision": observed_rev,
        "model_revision_verification": revision_source,
        "all_exact_guard_top10": False,
        "track_result": {},
        "claim_boundary": "CPU mismatch is diagnostic; MPS exact agreement requires source-compatible versions and input.",
    }
    for track, (q_emb, p_emb, ids) in tracks.items():
        raw_score = q_emb @ p_emb.T
        raw_rankings = rank_top11(raw_score, query_ids, ids)
        write_jsonl(args.out / (track + "_RAW_fresh.jsonl"), [
            {"query_id": qid, "top_scored": [{"electronics_id": id, "score": score} for id, score in vals]}
            for qid, vals in raw_rankings
        ])
        done, equal10, equal1, max_diff = 0, 0, 0, 0.
        with (args.out / (track + "_GUARD_fresh.jsonl")).open("w", encoding="utf-8") as f:
            for eps in EPS:
                if eps_to_repr_spec(eps, 768).proj_dim != (128,160,192,224,256,320,768)[EPS.index(eps)]:
                    raise ValueError("GUARD_REPRESENTATION_SCHEDULE_DRIFT")
                for seed in SEEDS:
                    q_guard = apply_guard_repr(q_emb, eps, seed)
                    p_guard = apply_guard_repr(p_emb, eps, seed)
                    guarded = q_guard @ p_guard.T
                    found = rank_top11(guarded, query_ids, ids)
                    n10, n1, score_err = compare_guard(track, eps, seed, found, ref[track])
                    done += len(query_ids)
                    equal10 += n10
                    equal1 += n1
                    max_diff = max(max_diff, score_err)
                    for qid, values in found:
                        f.write(json.dumps({
                            "track":track,"epsilon":eps,"seed":seed,"query_id":qid,
                            "top_scored":[{"rank":j+1,"electronics_id":id,"score":score}
                                          for j,(id,score) in enumerate(values)]
                        }, ensure_ascii=False) + "\n")
                    print(f"{track}: eps={eps}, seed={seed}, exact_top10={n10}/30", flush=True)
        report["track_result"][track] = {
            "comparisons": done,
            "top10_exact": equal10,
            "top1_exact": equal1,
            "max_abs_common_score_difference": max_diff,
            "exact_top10_pass": equal10 == done,
        }
    report["all_exact_guard_top10"] = all(x["exact_top10_pass"] for x in report["track_result"].values())
    (args.out / "comparison_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("RESULT_REPORT=", args.out / "comparison_report.json")
    print("ALL_EXACT_GUARD_TOP10=", report["all_exact_guard_top10"])
    print("NOTE: fresh results have not overwritten frozen references.")


if __name__ == "__main__":
    main()
