#!/usr/bin/env python3
"""Check published frozen AGGREGATE result consistency only.

This does not regenerate embeddings, search rankings, human judgments,
bootstrap samples, or full scientific experiments.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "electronics"


def read_json(relative: str):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, tolerance: float = 1e-10):
    check(abs(actual - expected) <= tolerance, f"{actual} != {expected}")


def main():
    prefix = "human_gt/v1/scientific_results/"
    ni = read_json(prefix + "track_b_noninferiority.json")
    b1 = read_json(prefix + "track_b_omfr.json")
    cp = read_json(prefix + "track_c_primary_omfr.json")
    cb = read_json(prefix + "track_c_broad_omfr.json")
    summary = read_json(prefix + "track_b_utility_summary.json")

    check(ni["16"]["query_denominator"] == 27, "Main denominator")
    close(ni["16"]["raw_mean_ndcg_at_10"], 0.38275039558409096)
    close(ni["16"]["guard_mean_ndcg_at_10"], 0.4310907629777437)
    close(
        ni["16"]["delta_mean"],
        ni["16"]["guard_mean_ndcg_at_10"] - ni["16"]["raw_mean_ndcg_at_10"],
    )
    check(ni["16"]["retention_decisions"]["95%"]["retained"], "95% NI eps16")
    check(not ni["8"]["retention_decisions"]["95%"]["retained"], "95% NI eps8")
    check(ni["64"]["retention_decisions"]["95%"]["retained"], "95% NI eps64")

    for name, record, covered, total in [
        ("B1", b1, 457, 540),
        ("C-primary", cp, 336, 450),
        ("C-broad", cb, 342, 450),
    ]:
        check(record["covered_transition_count"] == covered, f"{name} covered")
        check(record["eligible_transition_count"] == total, f"{name} eligible")
        close(record["overall_coverage"], covered / total)
        check(record["coverage_gate_pass"] is False, f"{name} gate must fail")
    check("covered" in summary and "RAW" in summary["covered"], "Utility summary")

    ranking = BASE / (
        "ranking_propagation/v1/scientific_results/ranking_pair_summary.csv"
    )
    with ranking.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    b1pairs = [row for row in rows if row["track"] == "B1_anchor"]
    check(len(b1pairs) == 6, "B1 adjacent pair count")
    check(
        [(int(r["epsilon_from"]), int(r["epsilon_to"])) for r in b1pairs]
        == [(0, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64)],
        "B1 epsilon order",
    )
    check(
        [int(row["top1_flip_count"]) for row in b1pairs]
        == [87, 85, 68, 72, 73, 62],
        "B1 Top-1 flips",
    )

    robustness = BASE / (
        "ranking_propagation/v1/scientific_results/same_epsilon_seed_robustness.csv"
    )
    with robustness.open(encoding="utf-8", newline="") as stream:
        robustness_rows = list(csv.DictReader(stream))
    check(
        sum(r["track"] == "B1_anchor" for r in robustness_rows) == 7,
        "B1 same-epsilon entries",
    )

    figure_data = read_json("human_gt/v1/manuscript_v1/figure_source_data.json")
    figure_guards = figure_data["track_b_utility"]["guard"]
    check([x["epsilon"] for x in figure_guards] == [0, 2, 4, 8, 16, 32, 64],
          "Figure utility epsilons")
    close(figure_data["track_b_utility"]["raw_ndcg_at_10"],
          ni["16"]["raw_mean_ndcg_at_10"])
    for entry in figure_guards:
        x = ni[str(entry["epsilon"])]
        close(entry["ndcg_at_10"], x["guard_mean_ndcg_at_10"])
        check(entry["retained_95"] == x["retention_decisions"]["95%"]["retained"],
              "Figure noninferiority decision")
    for label, record in [("Track B", b1), ("Track C PRIMARY", cp),
                          ("Track C BROAD", cb)]:
        by_pair = record["pair_coverage"]
        supplied = figure_data["omf_coverage"]["tracks"][label]
        check(len(supplied) == 6, "Figure pair coverage")
        for key, observed in zip(figure_data["omf_coverage"]["pairs"], supplied):
            close(observed, by_pair[key])

    print("PASS: frozen aggregate checks.")
    print("B1 Raw nDCG@10 0.382750; Guard epsilon=16 0.431091.")
    print("B1/C-primary/C-broad available coverage: 457/540, 336/450, 342/450.")
    print("All coverage gates FAIL; OMFR remains available-case exploratory.")
    print("WARNING: this verifies published aggregates, NOT full scientific reproduction.")


if __name__ == "__main__":
    main()
