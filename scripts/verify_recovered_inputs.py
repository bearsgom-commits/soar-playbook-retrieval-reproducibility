#!/usr/bin/env python3
"""Check frozen 4 JSONL inputs by exact size, SHA-256, record counts; do not expose text.

Usage: python scripts/verify_recovered_inputs.py /path/to/input/folder

This is NOT end-to-end scientific experiment replay or release-rights approval.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "playbook_source_clean_inputs.jsonl": (7874230, 1606, "bafbf21b08f70de1355ea5bb985c4e57421fd35d56deb77b639dc4e168c94d89"),
    "query_source_clean_inputs.jsonl": (12226, 30, "e72be8067f94bf72c69d6cb69e9cbd3e431a8153e1c5ade468283fa9040c453c"),
    "anchor_50_clean_binding.jsonl": (24617, 50, "c404fea3d583a61932c0ca5a0c33212575acd5215468e8490367991c789f237b"),
    "token_lengths.jsonl": (781316, 1766, "9732e3ba440d42397e09a629d648f4c4e573bcc8ef2aac6a0fe63d3b3e31c14a"),
}

def main(directory: Path) -> int:
    passed = 0
    for name, (size, count, sha256) in EXPECTED.items():
        path = directory / name
        if not path.is_file():
            print(f"FAIL {name}: not present")
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        try:
            rows = [json.loads(line) for line in data.splitlines()]
            valid_rows = len(rows) == count and all(isinstance(row, dict) for row in rows)
        except (ValueError, UnicodeError):
            valid_rows = False
            rows = []
        ok = len(data) == size and digest == sha256 and valid_rows
        print(f"{'PASS' if ok else 'FAIL'} {name}: bytes={len(data)}, records={len(rows)}, sha256={digest}")
        passed += int(ok)
    print(f"STATUS {passed}/4. File integrity only; no raw data uploaded or model rerun.")
    return 0 if passed == 4 else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.input_dir))
