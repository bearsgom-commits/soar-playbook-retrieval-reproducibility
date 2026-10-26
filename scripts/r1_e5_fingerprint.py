#!/usr/bin/env python3
"""R1 diagnostic: input/tokenizer/weight fingerprint; no embedding or Guard rerun."""
from pathlib import Path
import hashlib
import json
import sys
import platform
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rerun_e5_guard_from_frozen_inputs import prepare_inputs, MODEL_ID, MODEL_REV

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    inputs = Path(sys.argv[1])
    out = Path(sys.argv[2])
    plan, _, _, _ = prepare_inputs(inputs)
    model = SentenceTransformer(MODEL_ID, revision=MODEL_REV, device="cpu")
    query_id = plan["query_ids"][0]
    query = plan["arrays"]["C_query"][0]
    assert query_id == "Q01"
    ids = model.tokenizer(query, add_special_tokens=True, truncation=True, max_length=512)["input_ids"]
    hashes = {}
    for filename in ("config.json", "model.safetensors", "pytorch_model.bin"):
        try:
            path = hf_hub_download(repo_id=MODEL_ID,filename=filename,revision=MODEL_REV,local_files_only=True)
            hashes[filename] = sha256(path)
        except Exception:
            hashes[filename] = "NOT_FOUND"
    if hashes["model.safetensors"] == "NOT_FOUND":
        raise RuntimeError("PINNED_MODEL_WEIGHT_NOT_FOUND")
    report = {
        "model_id": MODEL_ID, "model_revision": MODEL_REV,
        "platform": platform.platform(), "query_id": query_id,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "query_length": len(query), "token_count": len(ids),
        "token_sha256": hashlib.sha256(json.dumps(ids,separators=(",",":")).encode()).hexdigest(),
        "token_ids": ids, "model_files": hashes,
        "max_seq_length": model.max_seq_length,
        "default_prompt_name": model.default_prompt_name
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "r1_ci_fingerprint.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    for key in ("query_sha256","token_count","token_sha256","model_files","max_seq_length"):
        print(f"{key.upper()}={report[key]}",flush=True)
    print("STATUS=PASS_R1_CI_FINGERPRINT",flush=True)

if __name__=="__main__":
    main()
